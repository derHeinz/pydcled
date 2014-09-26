import usb.core

class LED(object):
    
    DeviceVendor = 0x1d34
    DeviceProduct = 0x0013
    
    def _acquiredevice(self):
        # find our device
        self.device = usb.core.find(
        #    backend = usb.backend.libusb0.get_backend(),
            idVendor = self.DeviceVendor,
            idProduct = self.DeviceProduct
        )
    
        detachkerneldriver = True
    
        # Check whether we need to detach the kernel driver
        try:
            if self.device.is_kernel_driver_active(0) == False:
                detachkerneldriver = False
        # In some supported pyusb backend libraries, this method isn't implemented
        # In which case, we may as well just try to detach the kernel driver.
        except NotImplementedError:
            detachkerneldriver = True
    
        if detachkerneldriver == True:
            try:
                self.device.detach_kernel_driver(0)
            # If we're trying to detach the kernel driver with no information (because
            # the checking method wasn't implemented), it'll throw this error
            except usb.core.USBError:
                pass
        
        self.running = True

    def __init__(self):
        self.device = False
        self.brightness = 0
        self.running = False
        self._acquiredevice()

   
    # Takes an ascii representation of the screen, and converts it into a set of bytes
    # suitable to send via USB
    def packascii(self, screen, litchar='x'):
        # strip out all newlines, in case they were using those to format the string
        screen = screen.replace("\n", '').lower()
        rows = []
        for i in range(7):
            rowbytes = []
            # Grab a slice of 21 characters, and pad it out to 24 by adding three 'x's to the end
            row = screen[(0+i*21):(21+i*21)] + '...'
            # Now grap slices of that, 8 characters at a time, and convert them to bytes
            bytenum = 0
            byteval = 0
            for j in range(24):
                bitnum = j % 8
                if (row[j] != litchar):
                    bitval = 2 ** bitnum
                else:
                    bitval = 0
                byteval += bitval
                
                if bitnum == 7:
                    bytenum += 1
                    rowbytes.insert(0, byteval)
                    byteval = 0
            rows.append(rowbytes)
        
        #Add an empty "row 8" to round off the size of the fourth packet
        rows.append([0xFF] * 3)
    
        packets = []
        for i in range(0,7,2):
            packet = []
            # brightness (0, 1, or 2; 0 = brightest)
            packet.append(self.brightness)
            # row number
            packet.append(i)
            for j in range(2):
                for k in range(3):
                    packet.append(rows[i+j][k])
            packets.append(packet)
        return packets
    #        print "\n"

    # Data should be an array of packets ready to send to the device
    def sendtoled(self, data):
        for packet in data:
            self.device.ctrl_transfer(
                bmRequestType = 0x21,
                bRequest = 0x09,
                wValue = 0x0000,
                wIndex = 0x0000,
                data_or_wLength = packet
            )


    def showascii(self, screen, litchar='x'):
        self.sendtoled(self.packascii(screen, litchar))