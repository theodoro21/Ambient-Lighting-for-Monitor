import time
import struct
import serial
import Quartz.CoreGraphics as CG
 
 
class ScreenShot(object):
    """Captures the screen using CoreGraphics, and provides access to
    the pixel rgba values.
    """
 
    def capture(self, region = None):
        """region should be a CGRect, something like:
 
        >>> import Quartz.CoreGraphics as CG
        >>> region = CG.CGRectMake(0, 0, 100, 100)
        >>> sp = ScreenPixel()
        >>> sp.capture(region=region)
 
        The default region is CG.CGRectInfinite (captures the full screen)
        """
 
        if region is None:
            region = CG.CGRectInfinite
        else:
            # TODO: Odd widths cause the image to warp. This is likely
            # caused by offset calculation in ScreenPixel.pixel, and
            # could could modified to allow odd-widths
            if region.size.width % 2 > 0:
                emsg = "Capture region width should be even (was %s)" % (
                    region.size.width)
                raise ValueError(emsg)
 
        # Create screenshot as CGImage
        image = CG.CGWindowListCreateImage(
            region,
            CG.kCGWindowListOptionOnScreenOnly,
            CG.kCGNullWindowID,
            CG.kCGWindowImageDefault)
 
        # Intermediate step, get pixel data as CGDataProvider
        prov = CG.CGImageGetDataProvider(image)
 
        # Copy data out of CGDataProvider, becomes string of bytes
        self._data = CG.CGDataProviderCopyData(prov)
 
        # Get width/height of image
        self.width = CG.CGImageGetWidth(image)
        self.height = CG.CGImageGetHeight(image)
        print "Width = ", self.width
        print "Height = ", self.height
        

    def pixel(self, x, y):
        """Get pixel value at given (x,y) screen coordinates
 
        Must call capture first.
        """
 
        # Pixel data is unsigned char (8bit unsigned integer),
        # and there are for (blue,green,red,alpha)
        data_format = "BBBB"
 
        # Calculate offset, based on
        # http://www.markj.net/iphone-uiimage-pixel-color/
        offset = 4 * ((self.width*int(round(y))) + int(round(x)))
 
        # Unpack data from string into Python'y integers
        b, g, r, a = struct.unpack_from(data_format, self._data, offset=offset)
 
        # Return BGRA as RGBA
        return (r, g, b, a)


    def averageColorInRegion(self,x1,y1,x2,y2,skip_factor):
        """
            Will average the rgba values in the specified region.  
            Must first call capture() so there is an image available.

            skip_factor tells function to skip pixels. 
            Shortens computation time.
            e.g. skip_factor = 2, every other pixel will be skipped

        """

        rgb = [0, 0, 0, 0]
        temp = [0, 0, 0, 0]
        pixels = ((x2-x1) / skip_factor) * ((y2-y1) / skip_factor)

        for i in range(x1, x2, skip_factor):
            for j in range(y1, y2, skip_factor):
                temp = self.pixel(i, j)
                rgb[0] += temp[0]
                rgb[1] += temp[1]
                rgb[2] += temp[2]
                rgb[3] += temp[3]

        '''
        print "[%s,%s]" % (i,j)
        print "Red: ", rgb[0] / pixels
        print "Green: ", rgb[1] / pixels
        print "Blue: ", rgb[2] / pixels
        '''

        for i in range(4):
            rgb[i] = rgb[i]/pixels
        return rgb


if __name__ == '__main__':
    # configure the serial connections (the parameters differs on the device you are connecting to)
    port = serial.Serial(port = "/dev/tty.usbserial-A103VO60", baudrate = 115200, writeTimeout = 0)
    port.close()
    port.open()


    count = 0
    skip_factor = 10
    section_color = [[0 for x in range(3)] for x in range(7)] 
    screen = ScreenShot()  #Create ScreenPixel object

    # Timer helper-function
    import contextlib
 
    @contextlib.contextmanager
    def timer(msg):
        start = time.time()
        yield
        end = time.time()
        print "%s: %.02fms" % (msg, (end-start)*1000)

 
    while (1):

        with timer("Capture"):
            screen.capture()    # Take screenshot (takes about 30ms for me)
     
        #Average the color of different sections of the screenshot
        with timer("Averaging Colors in Sections"):
            section_color[0] = screen.averageColorInRegion(screen.width - 300, screen.height/2, screen.width, screen.height, skip_factor)
            section_color[1] = screen.averageColorInRegion(screen.width - 300, 0, screen.width, screen.height/2, skip_factor)
            section_color[2] = screen.averageColorInRegion(screen.width*2/3, 0, screen.width, 300, skip_factor)
            section_color[3] = screen.averageColorInRegion(screen.width/3, 0, screen.width*2/3, 300, skip_factor)
            section_color[4] = screen.averageColorInRegion(0, 0, 960, 300, skip_factor)
            section_color[5] = screen.averageColorInRegion(0, 0, 300, screen.height/2, skip_factor)
            section_color[6] = screen.averageColorInRegion(0, screen.height/2, 300, screen.height, skip_factor)
            
            if (port.isOpen()):
                header = 's'
                port.write(chr(115))
                print "Writing header:", ord(header), header
                for i in range(7):
                    for j in range(3):
                        #if (section_color[i][j] < 50):
                        #    section_color[i][j] = section_color[i][j] / 4 #make the blacks blacker
                        print "Writing Port: ", section_color[i][j]
                        port.write(chr(section_color[i][j]))
                        #port.write(chr(255))

            #print "Attempting to read Port: ", port.inWaiting()
            #if (port.inWaiting()):
            #    print "From Port: ", port.read(1)


            '''
            with timer("Upper Left"):
                screen.averageColorInRegion(0, 0, 960, 300, 5)
            print ""
            
            with timer("Upper Middle"):
                screen.averageColorInRegion(screen.width/3, 0, screen.width*2/3, 300, 5)
            print ""
            
            with timer("Upper Right"):
                screen.averageColorInRegion(screen.width*2/3, 0, screen.width, 300, 5)
            print ""
            
            with timer("Left Upper"):
                screen.averageColorInRegion(0, 0, 300, screen.height/2, 5)
            print ""
            
            with timer("Left Lower"):
                screen.averageColorInRegion(0, screen.height/2, 300, screen.height, 5)
            print ""
            
            with timer("Right Upper"):
                screen.averageColorInRegion(screen.width - 300, 0, screen.width, screen.height/2, 5)
            print ""
            
            with timer("Right Lower"):
                screen.averageColorInRegion(screen.width - 300, screen.height/2, screen.width, screen.height, 5)
            print ""
            '''

               
            count += 1
            print "" 
            # To verify screen-cap code is correct, save all pixels to PNG,
            # using http://the.taoofmac.com/space/projects/PNGCanvas
            
    #port.close()    #Close serial port


        '''
        from pngcanvas import PNGCanvas
        c = PNGCanvas(screen.width, screen.height)
        
        for x in range(screen.width):
            for y in range(screen.height):
                c.point(x, y, color = screen.pixel(x, y))
     

        for x in range(screen.width - 300, screen.width):
            for y in range(screen.height/2, screen.height):
                c.point(x, y, color = section_color[0])
        for x in range(screen.width - 300, screen.width):
            for y in range(0, screen.height/2):
                c.point(x, y, color = section_color[1])

        for x in range(screen.width*2/3, screen.width):
            for y in range(0, 300):
                c.point(x, y, color = section_color[2])
        for x in range(screen.width/3, screen.width*2/3):
            for y in range(0, 300):
                c.point(x, y, color = section_color[3])
        for x in range(0, screen.width/3):
            for y in range(0, 300):
                c.point(x, y, color = section_color[4])

        for x in range(0, 300):
            for y in range(0, screen.height/2):
                c.point(x, y, color = section_color[5])
        for x in range(0, 300):
            for y in range(screen.height/2, screen.height):
                c.point(x, y, color = section_color[6])

        with open("test.png", "wb") as f:
            f.write(c.dump())
            
        '''




