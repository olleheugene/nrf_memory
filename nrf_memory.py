"""
==================================================================================
nRF Memory external flash read/writer
==================================================================================
COMMAND:
    read                 Read binary from the given QSPI's address
    write                Write binary to the given QSPI's address
    test                 Memory test 
    
Options:
    -h, --help           Show this screen and exit
    -v, --version        Show version
    --saddr=<n>          Start address
    --size=<n>           Reading size
    --ofile=<filename>   Output binary file name
    --ifile=<filename>   Input binary file name
    --serial=<n>         J-link serial number. If not set, listing or set automatically
    --conf=<filename>    Configuration File
    --dump=<n>           Enable/Disable hex-dump (true=enable, false=disable)
    --pattern=<pattern>  4Bytes test pattern (default:0x55555555)
    --fulltest=<n>       Test whole memory (true=enable, false=disable)
    --family=<device>    Device Family (NRF52, NRF53, NRF91). If not set, set automatically
----------------------------------------------------------------------------------
Usage: 
    nrf_memory COMMAND [--family=<DeviceFamily>] [--saddr=<startaddress>] [--size=<n>] [--ofile=<filename>.bin] [--ifile=<filename>.bin] [--serial=<serialno.>] [--conf=<ini_file>] [--dump=<n>] [--pattern=<pattern>] [--fulltest=<n>]
    nrf_memory (-h | --help | -v | --version)

Example:
    $ nrf_memory read --saddr=0x1200 --size=4096 --ofile=memorydata.bin
    $ nrf_memory write --ifile=memory.bin
    $ nrf_memory test --pattern=0x55555555
----------------------------------------------------------------------------------
"""
VERSION      = "\nnrf_memory" + " v0.6"
BLOCKSIZE    = 4096
QSPIREADSIZE = 4096 * 10

TYPE_READ  = 1
TYPE_WRITE = 2
TYPE_TEST  = 3
    
from docopt import docopt, DocoptExit
from pynrfjprog import LowLevel
import sys
import os
import cmd
from time import sleep
from progress.bar import Bar

configtoml=dict()

config = dict()
config['startaddr']        = '0x0'
config['size']             = 65536
config['outputfile']       = 'omemory_data.bin'
config['inputfile']        = 'imemory_data.bin'
config['serial']           = ''
config['family']           = 'AUTO'
config['conf']             = 'QspiDefault.ini'
config['dumpmode']         = 'FALSE'
config['pattern']          = '0x55555555'
config['fulltest']         = 'FALSE'
config['testcount']        = 10

# Command Line Interface
def docopt_cmd(func):
    """
    This decorator is used to simplify the try/except block and pass the result
    of the docopt parsing to the called action.
    """
    def fn(self, arg):
        try:
            opt = docopt(fn.__doc__, arg, version=VERSION)

        except DocoptExit as e:
            # The DocoptExit is thrown when the args do not match.
            # We print a message to the user and the usage block.

            print('Invalid Command!')
            print(e)
            return

        except SystemExit:
            # The SystemExit exception prints the usage for --help
            # We do not need to do the print here.
            return

        return func(self, opt)

    fn.__name__ = func.__name__
    fn.__doc__ = func.__doc__
    fn.__dict__.update(func.__dict__)
    return fn


# Interactive Command Line Tool
class CLI (cmd.Cmd):
    deviceFamily = 0

    def print_err(self, message):
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(message)
        print("\r!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    def is_hexadecimal(self,s):
        return s.isdigit()

    def config(self,arg, type):
        if(arg['--saddr']):
            config['startaddr']        = arg['--saddr']
        if(arg['--size']):
            if(arg['--size'].isdigit()):
                config['size'] = int(arg['--size'])
            else:
                config['size'] = int(arg['--size'],16)
        if(arg['--serial']):
            config['serial']           = arg['--serial']
        if(arg['--family']):
            config['family']           = arg['--family']
        if(arg['--conf']):
            config['conf']             = arg['--conf']

        if(str(config['family']).upper() == 'NRF53'):
            self.deviceFamily = LowLevel.DeviceFamily.NRF53
        elif (str(config['family']).upper() == 'NRF52'):
            self.deviceFamily = LowLevel.DeviceFamily.NRF52
        elif (str(config['family']).upper() == 'NRF91'):
            self.deviceFamily = LowLevel.DeviceFamily.NRF91
        else:
            self.deviceFamily = LowLevel.DeviceFamily.AUTO

        if(type == TYPE_READ):
            if(arg['--ofile']):
                config['outputfile']       = arg['--ofile']
            if(arg['--dump']):
                config['dumpmode']         = arg['--dump'].upper()
        elif(type == TYPE_WRITE):
            if(arg['--ifile']):
                config['inputfile']        = arg['--ifile']
        elif(type == TYPE_TEST):
            if(arg['--pattern']):
                config['pattern']          = arg['--pattern']
            if(arg['--fulltest']):
                config['fulltest']         = arg['--fulltest'].upper()        

    @docopt_cmd
    def do_read(self, arg):
        """
    Usage: read [--family=<DeviceFamily>] [--saddr=<startaddress>] [--size=<n>] [--ofile=<filename>.bin] [--serial=<serialno.>] [--conf=<ini_file>] [--dump=<n>]
        """
        self.config(arg,TYPE_READ)

        with LowLevel.API(self.deviceFamily) as api:
            newFile = open(config['outputfile'], "wb")  
            try:
                # Connect and halt target core
                if (config['serial']):
                    api.connect_to_emu_with_snr(int(config['serial']))
                else:
                    api.connect_to_emu_without_snr()
                # api.connect_to_device()
                api.halt()
                api.disable_bprot()
                api.qspi_init_ini(config['conf'])

                print("--------------------- Parameters -----------------------")
                print("Device Family   \t: %s" % api.read_device_family())
                print("Debugger Serial \t: %s" % api.read_connected_emu_snr())
                print("Start address   \t: %s" % str(config['startaddr']))
                print("Read Size       \t: %s(%s) Byte(s)" % (str(config['size']),hex(config['size'])))
                print("Output File     \t: %s" % str(config['outputfile']))
                if(config['dumpmode'] == 'TRUE'):
                    dumpfile,ext=os.path.splitext(config['outputfile'])
                    print("Dump File       \t: %s_dump.txt" % (dumpfile))
                print("Config File     \t: %s" % str(config['conf']))
                print("--------------------------------------------------------")
            except Exception as error:
                self.print_err(error)
                sys.exit(1)

            print("Reading from target...")
            data = b''
            dumpdata = b''
            # api.qspi_configure_ini('QspiDefault.ini')
            addr = int(config['startaddr'],16)
            if(config['dumpmode'] == 'TRUE'):
                filename,ext=os.path.splitext(config['outputfile'])

            with Bar('Reading', width=50, fill='#', suffix='%(percent).1f%%',max=config['size']) as bar:
                try:

                    for addr in range(addr, config['size'], QSPIREADSIZE):
                        data = api.qspi_read(addr, QSPIREADSIZE) # Reading
                        newFile.write(data)
                        bar.index = addr
                        dumpdata += data
                        bar.update()
                    bar.index = addr+QSPIREADSIZE
                    bar.update()

                    if(config['dumpmode'] == 'TRUE'):
                        hex_dump(dumpdata, int(config['startaddr'],16), dumpfile=(filename+'_dump'+'.txt'))
                except Exception as error:
                    self.print_err(error)
                    sys.exit(1)
            print("Reading Done")
            
            sys.exit(0)

    @docopt_cmd
    def do_write(self, arg):
        """
    Usage: COMMAND [--family=<DeviceFamily>] [--saddr=<startaddress>] [--size=<n>] [--ifile=<filename>.bin] [--serial=<n>] [--conf=<ini_file>]
        """
        self.config(arg,TYPE_WRITE)

        tot_len = 0
        with LowLevel.API(config['family']) as api:
            try:
                # Connect and halt target core
                if (config['serial']):
                    api.connect_to_emu_with_snr(int(config['serial']))
                else:
                    api.connect_to_emu_without_snr()
                # api.connect_to_device()
                api.halt()
                api.disable_bprot()
                api.qspi_init_ini(config['conf'])

                print("--------------------- Parameters -----------------------")
                print("Device Family   \t: %s" % api.read_device_family())
                print("Debugger Serial \t: %s" % api.read_connected_emu_snr())
                print("Start address   \t: %s" % str(config['startaddr']))
                print("Input File      \t: %s" % str(config['inputfile']))
                print("File Size       \t: %s(%s) Byte(s)" % (str(os.path.getsize(config['inputfile'])),hex(os.path.getsize(config['inputfile']))))
                print("Config File     \t: %s" % str(config['conf']))
                print("-------------------------------------------------------")
            except Exception as error:
                self.print_err(error)
                sys.exit(1)
            
            print("Writing binary to target...")
            r_bin = bytes()
            if os.path.isfile(config['inputfile']):
                numofblocks, remain = divmod(int(os.path.getsize(config['inputfile'])), BLOCKSIZE)
                erasePageaddr = int(config['startaddr'],16)
                if(remain) :
                    numofblocks+=1

                print("Erasing %s blocks in flash..." % numofblocks)
                for i in range(numofblocks+1):
                    api.qspi_erase(erasePageaddr + (i * BLOCKSIZE), LowLevel.QSPIEraseLen.ERASE4KB)

                with open(config['inputfile'], 'rb') as file:
                    # while buf := file.read(1024): # Requires Python 3.8 or later 
                    while True:
                        buf = file.read(1024)
                        r_bin += buf
                        if not buf:
                            break
                print("Writing %s Byte(s)..." % str(len(r_bin)))
                api.qspi_write(int(config['startaddr'],16), r_bin)

            print("Writing Done")
            sys.exit(0)


    @docopt_cmd
    def do_test(self, arg):
        """
    Usage: test [--family=<DeviceFamily>] [--saddr=<startaddress>] [--size=<n>] [--serial=<serialno.>] [--conf=<ini_file>] [--pattern=<pattern>] [--fulltest=<n>]
        """
        self.config(arg,TYPE_TEST)

        with LowLevel.API(self.deviceFamily) as api:
            try:
                # Connect and halt target core
                if (config['serial']):
                    api.connect_to_emu_with_snr(int(config['serial']))
                else:
                    api.connect_to_emu_without_snr()

                api.halt()
                api.disable_bprot()
                api.qspi_init_ini(config['conf'])

                print("--------------------- Parameters -----------------------")
                print("Device Family   \t: %s" % api.read_device_family())
                print("Debugger Serial \t: %s" % api.read_connected_emu_snr())
                print("Start address   \t: %s" % str(config['startaddr']))
                if(config['fulltest'] == 'TRUE'):
                    print("Size            \t: %s(%s) Byte(s)" % (str(api.qspi_get_size()),hex(api.qspi_get_size())))
                else:
                    print("Size            \t: %s(%s) Byte(s)" % (str(config['size']),hex(config['size'])))
                print("Config File     \t: %s" % str(config['conf']))
                print("Test pattern    \t: %s" % config['pattern'])
                print("--------------------------------------------------------")

            except Exception as error:
                self.print_err(error)
                sys.exit(1)

            pattern_int = int(config['pattern'],16)
            writeVal = bytes(BLOCKSIZE)
            writeVal = writeVal.replace(b'\x00\x00\x00\x00', int(config['pattern'],16).to_bytes((pattern_int.bit_length() + 7) // 8, 'big'))
            print("Start Flash test...")
            if(config['fulltest'] == 'TRUE'):
                numofblocks, remain = divmod(api.qspi_get_size(), BLOCKSIZE)
                testAddress = 0
                erasePageaddr = 0
                verifyVal = b''
                j=0

                print("Erasing whole external flash area...")
                api.qspi_erase(0x0,LowLevel.QSPIEraseLen.ERASEALL)

                with Bar('Testing', width=50, fill='#', suffix='%(percent).1f%% - %(eta)ds',max=numofblocks) as bar:
                    for i in range(0,numofblocks):
                        try:
                            # api.qspi_erase(testAddress, LowLevel.QSPIEraseLen.ERASE4KB)
                            # sleep(0.1)
                            api.qspi_write(testAddress, writeVal)
                            sleep(0.1)
                            verifyVal = api.qspi_read(testAddress, BLOCKSIZE)
                            for j in range(BLOCKSIZE):
                                if writeVal[j] != verifyVal[j]:
                                    raise Exception("\rVerification fail at %s"%(hex(int(config['startaddr'],16)+testAddress+j)))
                            testAddress = erasePageaddr + (i * BLOCKSIZE)
                            bar.next()
                        except Exception as error:
                            self.print_err(error)
                            sys.exit(1)
                    bar.index = numofblocks
                    bar.update()
            else:
                numofblocks, remain = divmod(config['size'], BLOCKSIZE)
                erasePageaddr = int(config['startaddr'],16)
                if(remain) :
                    numofblocks+=1

                position,tmp = divmod(numofblocks,(config['testcount']))

                if(numofblocks >= config['testcount']):
                    with Bar('Testing', width=50, fill='#', suffix='%(percent).1f%%',max=config['testcount']) as bar:
                        bar.index = config['testcount']
                        for i in range(1,(config['testcount']+1)):
                            if(i == (config['testcount'])):
                                testAddress = (numofblocks * BLOCKSIZE) - BLOCKSIZE
                            elif(i == 1):
                                testAddress = erasePageaddr
                            else:
                                testAddress = erasePageaddr + (position * i * BLOCKSIZE) - BLOCKSIZE
                            try:
                                api.qspi_erase(testAddress, LowLevel.QSPIEraseLen.ERASE4KB)
                                sleep(0.1)
                                api.qspi_write(testAddress, writeVal)
                                verifyVal = api.qspi_read(testAddress, BLOCKSIZE)
                                for j in range(BLOCKSIZE):
                                    if writeVal[j] != verifyVal[j]:
                                        raise Exception("\rVerification fail at %s(Read: %s)"%(hex(int(config['startaddr'],16)+testAddress+j), hex(verifyVal[j])))
                                # print("(%d) 4KB verification success at %s"%(i,hex(testAddress)))
                                bar.index=i
                                bar.update()
                            except Exception as error:
                                self.print_err(error)
                                sys.exit(1)

                        bar.index = config['testcount']+1
                        bar.update()
                else:
                    print("Set the '--size' value more at least %s"%hex(config['testcount']*BLOCKSIZE))
                    sys.exit(1)
            print("Verification completed")
            sys.exit(0)

def hex_dump(buffer,start_offset=0, dumpfile='temp_dump.txt'):
    filedump = open(dumpfile, "wb")  
    filedump.write(dumpfile.encode('ascii')+str('(Binary Size:%s Byte(s))'%len(buffer)).encode('ascii')+'\n'.encode('ascii'))
    filedump.write(bytearray('='.encode('ascii') * 62 + '\n'.encode('ascii')))

    offset = 0

    while offset < len(buffer):
        # Offset
        filedump.write(bytearray((' %08X : ' % (offset + start_offset)).encode('ascii')))
        
        if ((len(buffer) - offset) < 0x10) is True:
            data = buffer[offset:]
        else:
            data = buffer[offset:offset + 0x10]

        # Hex Dump
        for hex_dump in data:
            filedump.write(bytearray(("%02X" % hex_dump).encode('ascii')))

        if ((len(buffer) - offset) < 0x10) is True:
            filedump.write(bytearray((' ' * (3 * (0x10 - len(data)))).encode('ascii')))

        filedump.write(bytearray(('  ').encode('ascii')))

        # Ascii
        for ascii_dump in data:
            if ((ascii_dump >= 0x20) is True) and ((ascii_dump <= 0x7E) is True):
                filedump.write(bytearray(chr(ascii_dump).encode('ascii')))
            else:
                filedump.write(bytearray('.'.encode('ascii')))

        offset = offset + len(data)
        filedump.write(bytearray('\n'.encode('ascii')))

    filedump.write(bytearray('\n'.encode('ascii') + '='.encode('ascii') * 62 + '\n'.encode('ascii')))

if __name__ == '__main__':
    if sys.argv[1:]:           
    #Command Line Interface part
        opt = docopt(__doc__, sys.argv[1:],version=VERSION)
        if opt['COMMAND'] == 'read':
            CLI().do_read(sys.argv[2:])
        elif opt['COMMAND'] == 'write':
            CLI().do_write(sys.argv[2:])
        elif opt['COMMAND'] == 'test':
            CLI().do_test(sys.argv[2:])
        else:
            print(__doc__)
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)

