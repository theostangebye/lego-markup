import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches
import matplotlib.font_manager as font_manager
import matplotlib as mpl

# Open the PDF file
pdf_path = 'instructions.pdf'
output_pdf_path = 'instructions_markup.pdf'
path = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
prop = font_manager.FontProperties(fname=path)
mpl.rcParams['font.family'] = prop.get_name()

ULCorner = [210,120] # down 210 pixels from top and over 120 pixels from left is ULCorner of grid.
stride = 46.5 # width of lego brick.
grid_size = 8 # number of bricks.

###### JONATHAN: Change figsize_instructions to match your booklet page size (i heard it might be 8.5x5 or something like that.) 
figsize_instructions = (8.5,11) # figure size of the instructions_markup.pdf.  This should be the same as your input pdf.
figsize = (8.5, 11) # this is the figure size of the color swatches.
DPI = 220 # Resolution of the output... if you think your markups look crappy... CRANK THIS UP

# Define the color dictionary
color_dict = {
    (21, 35, 46): (1, 'white'), #black
    (112, 61, 34): (2, 'white'), #reddish brown
    (91, 60, 14): (3, 'white'), #dark brown
    (180, 168, 142): (4, 'black'), #dark tan
    (255, 252, 214): (5, 'black'), #light nougat
    (134, 137, 130): (6, 'white'), #dark bluish gray
    (40, 92, 70): (7, 'white'), #dark green
    (186, 186, 114): (8, 'black'), #olive green
    (247, 176, 130): (9, 'black'), #nougat
    (255, 242, 190): (10, 'black'), #tan
    (241, 140, 62): (11, 'black'), #medium nougat
    (255, 255, 198): (12, 'black'), #yellowish green
    (255, 255, 255): (13, 'black'), #white
    (140, 30, 31): (14, 'white'), #dark red
    (202, 109, 14): (15, 'white'), #dark orange
    (255, 222, 81): (16, 'black'), #bright light orange
    (194, 222, 207): (17, 'black'), #sand green
    (238, 43, 25): (18, 'black'), #red
    (224, 255, 255): (19, 'black'), #light aqua
    (225, 184, 244): (20, 'black'), #lavender (rubber)
    (14, 160, 175): (21, 'white'), #dark turquoise
    (193, 198, 202): (22, 'black'), #light bluish gray
    (113, 140, 161): (23, 'white'), #sand blue
    (255, 206, 237): (24, 'black'), #bright pink
    (82, 230, 255): (25, 'black'), #medium azure
    (255, 168, 42): (26, 'black'), #orange
    (55, 150, 84): (27, 'white'), #green
    (29, 70, 114): (28, 'white'), #dark blue
    (255, 145, 144): (29, 'black'), #coral
    (255, 242, 76): (30, 'black'), #yellow
    (163, 229, 255): (31, 'black'), #bright light blue
    (118, 188, 247): (32, 'black'), #medium blue
    (206, 148, 222): (33, 'black'), #medium lavender
}

colors_observed = {}

pdf_document = fitz.open(pdf_path)
unknown_colors = []

# Loop through each page
with PdfPages(output_pdf_path) as pdf:
    # First we detect the color of each brick and put it in a grid_values list.
    for page_num in range(len(pdf_document)):
        print("Working on Page", page_num)
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_cv = np.array(img_pil) # convert to numpy from PIL image.

        grid_values = []
        grid_img = img_cv[ULCorner[0]:int(ULCorner[0] + grid_size * stride), ULCorner[1]:int(ULCorner[1] + grid_size * stride),:]
        for i in range(grid_size):
            for j in range(grid_size):
                tile = grid_img[int(i*stride):int((i+1)*stride),int(j*stride):int((j+1)*stride),:]

                color_rgb = np.median(tile, axis=0)
                color_rgb = np.median(color_rgb, axis=0)
                # print(f"\tDetected Tile {i*grid_size + j}, color: {color_rgb}")
                minval = 1e6
                mink = None
                for k in color_dict.keys():
                    keycolor = np.array(k)
                    distance = np.linalg.norm(color_rgb - keycolor)
                    if distance < minval:
                        minval = distance
                        mink = k
                        foreground = color_dict[k][1]
                        idx = color_dict[k][0]
                        if mink in colors_observed.keys():
                            colors_observed[mink] += 1
                        else:
                            colors_observed[mink] = 1
                if minval > 10:
                    # Color match not found...
                    foreground = 'red' # redd
                    idx = -99
                    unknown_colors.append(color_rgb)
                grid_values.append([idx,foreground])

        # Now, we draw the grid_values onto an image!
        fig, ax = plt.subplots(figsize=figsize_instructions, dpi=DPI)
        ax.imshow(img_pil)
        # Remove axes
        ax.axis('off')
        # Add 8x8 grid numbers
        for x in range(grid_size):
            for y in range(grid_size):
                tile_number = y * grid_size + x
                c = grid_values[tile_number][1]
                t = grid_values[tile_number][0]
                # print(f"Text: {t}, Color: {c}")
                ax.text(ULCorner[1] + x * (stride / 1) + stride/2, ULCorner[0] + y * (stride / 1) + stride/2 + 3, str(t),
                        color=c, fontsize=16, ha='center', va='center')

        # Save the figure as a PDF without borders
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        pdf.savefig(fig, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
print(f'Saved {pdf_path}')

unknown_colors_all = np.array(unknown_colors)
unknown_colors = np.unique(unknown_colors_all,axis=0)

for unk in unknown_colors_all:
    tunk = tuple(unk)
    print(tunk)
    if tunk in colors_observed.keys():
        colors_observed[tunk] += 1
    else:
        colors_observed[tunk] = 1

## Now make a swatch report for Jacob. :)
# Create a new PDF with ReportLab
# Create a PDF with matplotlib
pdf_file = "color_swatches.pdf"
with PdfPages(pdf_file) as pdf:
    fig, ax = plt.subplots(figsize=figsize, dpi=DPI)  # Letter size page
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 11)
    ax.axis('off')

    swatch_size = .75  # Size of each swatch
    padding = 0.25  # Padding between swatches
    x, y = 1, 11  # Starting position

    for rgb, (number, text_color) in color_dict.items():
        # Draw the swatch
        rect = patches.Rectangle((x, y - swatch_size), swatch_size, swatch_size, linewidth=1, edgecolor='none', facecolor=[c/255.0 for c in rgb])
        ax.add_patch(rect)

        # Draw the number on the swatch
        ax.text(x + swatch_size / 2, y - swatch_size / 4, str(number), ha='center', va='center', color=text_color, fontsize=12)
        if tuple(rgb) in colors_observed.keys():
            num_observed = colors_observed[tuple(rgb)]
        else:
            num_observed = 0
        ax.text(x + swatch_size / 2, y - (3*swatch_size / 4), str(int(num_observed)), ha='center', va='center', color=text_color, fontsize=12)

        # Move to the next position
        x += swatch_size + padding
        if x + swatch_size > 8.5:
            x = 1
            y -= swatch_size + padding
            if y - swatch_size < 0:
                pdf.savefig(fig)
                plt.clf()
                fig, ax = plt.subplots(figsize=figsie ,dpi=DPI)
                ax.set_xlim(0, 8.5)
                ax.set_ylim(0, 11)
                ax.axis('off')
                x, y = 1, 10

    for rgb in unknown_colors:
        number = -99
        text_color = 'red'
        # Draw the swatch
        rect = patches.Rectangle((x, y - swatch_size), swatch_size, swatch_size, linewidth=1, edgecolor='none', facecolor=[c/255.0 for c in rgb])
        ax.add_patch(rect)

        # Draw the number on the swatch
        ax.text(x + swatch_size / 2, y - swatch_size / 4, str(number), ha='center', va='center', color=text_color, fontsize=12)
        if tuple(rgb) in colors_observed.keys():
            num_observed = colors_observed[tuple(rgb)]
        else:
            num_observed = 0
        ax.text(x + swatch_size / 2, y - (3*swatch_size / 4), str(int(num_observed)), ha='center', va='center', color=text_color, fontsize=12)

        # Move to the next position
        x += swatch_size + padding
        if x + swatch_size > 8.5:
            x = 1
            y -= swatch_size + padding
            if y - swatch_size < 0:
                pdf.savefig(fig)
                plt.clf()
                fig, ax = plt.subplots(figsize=figsie,  dpi=DPI)
                ax.set_xlim(0, 8.5)
                ax.set_ylim(0, 11)
                ax.axis('off')
                x, y = 1, 10

    pdf.savefig(fig)
    plt.close()
print("Saved",pdf_file)


# print(colors_observed)
