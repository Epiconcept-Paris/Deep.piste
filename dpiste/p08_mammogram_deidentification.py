import os
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader
from dpiste import dicom2png


def p08_001_anonymize_folder(indir, outdir):
    """
    Anonymize a complete directory of DICOM.

    @param

    indir = the initial directory of DICOM to de-identify
    outdir = the final director of DICOM which have been de-identied
    """
    start_time = time.time()
    nb_images_processed = 1
    summary = """\n\n\n
    Here is a summary of the DICOMs that have been de-identified ONLY.
    (The DICOMs that had no text area have been moved to the output directory
    so they are not listed in this file.)\n\n\n
    """
    for file in sorted(os.listdir(indir)):
    
        if indir.endswith("/"):
            input_path = indir + file
        else:
            input_path = indir + '/' + file
        
        dicom = dicom2png.dicom2narray(input_path)
        pixels = dicom[0]

        ocr_data = p08_002_get_text_areas(pixels)
        
        if not len(ocr_data):
            pixels = p08_003_hide_text(pixels, ocr_data)
        

        if outdir.endswith("/"):
            output_path = outdir  + os.path.basename(file)
            output_ds = outdir + os.path.basename(file) + ".txt"
            output_summary = outdir + "summary.log"
        else:
            output_path = outdir  + '/' + os.path.basename(file)
            output_ds = outdir + "/" + os.path.basename(file) + ".txt"
            output_summary = outdir + "/summary.log"

        with open(output_ds,'a') as f:
            file_path = indir + file
            print(file_path)
            f.write(file_path)
            f.write('/n')
            f.write(str(dicom[1]))
            f.write('/n')
            f.write(str(ocr_data))
            f.write('/n')
            f.write()

        summary = p08_004_update_summary(summary, file_path, ocr_data)

        dicom2png.narray2dicom(pixels, dicom[1], output_path)
        
        nb_images_processed += 1

    
        time_taken = time.time() - start_time
    with open(output_summary, 'w') as f:
        f.write(str(round(time_taken/60)) + " minutes taken to de-identify all images.")
        f.write(summary)




def p08_002_get_text_areas(pixels):
    """
    Easy OCR function. Gets an image at the path below and gets the 
    text of the picture. 
    """
    reader = Reader(['fr'])
    return reader.readtext(pixels)



def p08_003_hide_text(pixels, ocr_data, mode = "black"):
    """
    Get a NUMPY array, a list of the coordinates of the different text areas 
    in this array and (optional) a mode which can be : 
    blur" or "black". It returns the modified NUMPY array.

    MODES (optional):

    "black" mode (default) ==> add a black rectangle on the text areas
    "blur" mode            ==> blur the text areas
    """
    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))

    #Gets the coordinate of the top-left and the bottom-right points
    for found in ocr_data:
        #This condition avoids common false positives
        if found[1] != "" and len(found[1]) > 1:
            x1, y1 = int(found[0][0][0]), int(found[0][0][1])
            x2, y2 = int(found[0][2][0]), int(found[0][2][1])
            box = (x1,y1,x2,y2)
            
            #Applies a hiding effect
            if mode == "blur":
                cut = im.crop(box)
                for i in range(30):
                    cut = cut.filter(ImageFilter.BLUR)
                im.paste(cut, box)
            else:
                #Add a black rectangle on the targeted text
                draw = ImageDraw.Draw(im)

                #If the value is a tuple, the color has to be a tuple (RGB image)
                color = (0,0,0) if type(pixels[0][0]) == tuple else 0
                    
                draw.rectangle([x1, y1, x2, y2], fill=color)
                del draw

    return np.asarray(im)


def p08_004_update_summary(summary, file_path, ocr_data):
    summary += "\n" + file_path + "\n↪words : "
    ocr_words = []
    for found in ocr_data:
        if ' ' in found[1]:
            new_tuple = (found[0], found[1].replace(' ',''), found[2])
            ocr_data.remove(found)
            ocr_data.append(new_tuple)
        ocr_words.append(found[1])
    for found in sorted(ocr_words):
        summary += found.lower() + " |"
    return summary