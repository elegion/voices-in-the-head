

class Mp3(object):
    def __init__(self):
        self.fname = None
        self.fp = None
        self.type = None

        self.tsp = 0
        self.tsr = 0
        self.tsr0 = None

    def open(self, path):
        self.tsp = self.tsr = 0; self.tsr0 = None; self.type = type
        self.fp = open(path, 'rb')
        magic, version, flags, offset = struct.unpack('!3sBBI', self.fp.read(9))
        if _debug: print 'FLV.open() hdr=', magic, version, flags, offset
        if magic != 'FLV': raise ValueError('This is not a FLV file')
        if version != 1: raise ValueError('Unsupported FLV file version')
        if offset > 9: self.fp.seek(offset-9, os.SEEK_CUR)
        self.fp.read(4) # ignore first previous tag size
        return self

    def close(self):
        '''Close the underlying file for this object.'''
        if _debug: print 'closing flv file'
        if self.type == 'record' and self.tsr0 is not None: self.writeDuration((self.tsr - self.tsr0)/1000.0)
        if self.fp is not None: self.fp.close(); self.fp = None

    def delete(self, path):
        '''Delete the underlying file for this object.'''
        try: os.unlink(path)
        except: pass

    def writeDuration(self, duration):
        if _debug: print 'writing duration', duration
        output = amf.BytesIO()
        amfWriter = amf.AMF0(output)
        amfWriter.write('onMetaData')
        amfWriter.write({"duration": duration, "videocodecid": 2})
        output.seek(0); data = output.read()
        length, ts = len(data), 0
        data = struct.pack('>BBHBHB', Message.DATA, (length >> 16) & 0xff, length & 0x0ffff, (ts >> 16) & 0xff, ts & 0x0ffff, (ts >> 24) & 0xff) + '\x00\x00\x00' +  data
        data += struct.pack('>I', len(data))
        lastpos = self.fp.tell()
        if lastpos != 13: self.fp.seek(13, os.SEEK_SET)
        self.fp.write(data)
        if lastpos != 13: self.fp.seek(lastpos, os.SEEK_SET)

    def write(self, message):
        '''Write a message to the file, assuming it was opened for writing or appending.'''
#        if message.type == Message.VIDEO:
#            self.videostarted = True
#        elif not hasattr(self, "videostarted"): return
        if message.type == Message.AUDIO or message.type == Message.VIDEO:
            length, ts = message.size, message.time
            if _debug: print 'FLV.write()', message.type, ts
            if self.tsr0 is None: self.tsr0 = ts
            self.tsr, ts = ts, ts - self.tsr0
            # if message.type == Message.AUDIO: print 'w', message.type, ts
            data = struct.pack('>BBHBHB', message.type, (length >> 16) & 0xff, length & 0x0ffff, (ts >> 16) & 0xff, ts & 0x0ffff, (ts >> 24) & 0xff) + '\x00\x00\x00' +  message.data
            data += struct.pack('>I', len(data))
            self.fp.write(data)

    def reader(self, stream):
        '''A generator to periodically read the file and dispatch them to the stream. The supplied stream
        object must have a send(Message) method and id and client properties.'''
        if _debug: print 'reader started'
        try:
            while self.fp is not None:
                bytes = self.fp.read(11)
                if len(bytes) == 0:
                    response = Command(name='onStatus', id=stream.id, args=[dict(level='status',code='NetStream.Play.Stop', description='File ended', details=None)])
                    stream.send(response.toMessage())
                    break
                type, len0, len1, ts0, ts1, ts2, sid0, sid1 = struct.unpack('>BBHBHBBH', bytes)
                length = (len0 << 16) | len1; ts = (ts0 << 16) | (ts1 & 0x0ffff) | (ts2 << 24)
                body = self.fp.read(length); ptagsize, = struct.unpack('>I', self.fp.read(4))
                if ptagsize != (length+11):
                    if _debug: print 'invalid previous tag-size found:', ptagsize, '!=', (length+11),'ignored.'
                if stream is None or stream.client is None: break # if it is closed
                #hdr = Header(3 if type == Message.AUDIO else 4, ts if ts < 0xffffff else 0xffffff, length, type, stream.id)
                hdr = Header(0, ts, length, type, stream.id)
                msg = Message(hdr, body)
                # if _debug: print 'FLV.read() length=', length, 'hdr=', hdr
                # if hdr.type == Message.AUDIO: print 'r', hdr.type, hdr.time
                if type == Message.DATA: # metadata
                    amfReader = amf.AMF0(body)
                    name = amfReader.read()
                    obj = amfReader.read()
                    if _debug: print 'FLV.read()', name, repr(obj)
                stream.send(msg)
                if ts > self.tsp:
                    diff, self.tsp = ts - self.tsp, ts
                    if _debug: print 'FLV.read() sleep', diff
                    yield multitask.sleep(diff / 1000.0)
        except StopIteration: pass
        except:
            if _debug: print 'closing the reader', (sys and sys.exc_info() or None)
            traceback.print_exc()
            if self.fp is not None: self.fp.close(); self.fp = None

    def seek(self, offset):
        '''For file reader, try seek to the given time. The offset is in millisec'''
        if self.type == 'read':
            if _debug: print 'FLV.seek() offset=', offset, 'current tsp=', self.tsp
            self.fp.seek(0, os.SEEK_SET)
            magic, version, flags, length = struct.unpack('!3sBBI', self.fp.read(9))
            if length > 9: self.fp.seek(length-9, os.SEEK_CUR)
            self.fp.seek(4, os.SEEK_CUR) # ignore first previous tag size
            self.tsp, ts = int(offset), 0
            while self.tsp > 0 and ts < self.tsp:
                bytes = self.fp.read(11)
                if not bytes: break
                type, len0, len1, ts0, ts1, ts2, sid0, sid1 = struct.unpack('>BBHBHBBH', bytes)
                length = (len0 << 16) | len1; ts = (ts0 << 16) | (ts1 & 0x0ffff) | (ts2 << 24)
                self.fp.seek(length, os.SEEK_CUR)
                ptagsize, = struct.unpack('>I', self.fp.read(4))
                if ptagsize != (length+11): break
            if _debug: print 'FLV.seek() new ts=', ts, 'tell', self.fp.tell()

