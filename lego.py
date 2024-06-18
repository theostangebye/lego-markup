import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches

# Open the PDF file
pdf_path = 'instructions.pdf'
output_pdf_path = 'instructions_markup.pdf'

ULCorner = [210,120] # down 210 pixels from top and over 120 pixels from left is ULCorner of grid.
stride = 46.5 # width of lego brick.
grid_size = 8 # number of bricks.

# Define the color dictionary
color_dict = {
    (112, 61, 34): (1, 'black'),
    (136, 137, 131): (2, 'xkcd:blue'),  # Green square: Number 2, Black color for number
    (92, 59, 14): (3, 'xkcd:green'),  # Blue square: Number 3, White color for number
    # Add more color mappings as needed
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
        fig, ax = plt.subplots(figsize=(img_cv.shape[1] / 100, img_cv.shape[0] / 100), dpi=100)
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
                        color=c, fontsize=18, ha='center', va='center')

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
    fig, ax = plt.subplots(figsize=(8.5, 11))  # Letter size page
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
        ax.text(x + swatch_size / 2, y - (3*swatch_size / 4), str(int(colors_observed[rgb])), ha='center', va='center', color=text_color, fontsize=12)

        # Move to the next position
        x += swatch_size + padding
        if x + swatch_size > 8.5:
            x = 1
            y -= swatch_size + padding
            if y - swatch_size < 0:
                pdf.savefig(fig)
                plt.clf()
                fig, ax = plt.subplots(figsize=(8.5, 11))
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
        ax.text(x + swatch_size / 2, y - (3*swatch_size / 4), str(int(colors_observed[tuple(rgb)])), ha='center', va='center', color=text_color, fontsize=12)

        # Move to the next position
        x += swatch_size + padding
        if x + swatch_size > 8.5:
            x = 1
            y -= swatch_size + padding
            if y - swatch_size < 0:
                pdf.savefig(fig)
                plt.clf()
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.set_xlim(0, 8.5)
                ax.set_ylim(0, 11)
                ax.axis('off')
                x, y = 1, 10

    pdf.savefig(fig)
    plt.close()
print("Saved",pdf_file)


# print(colors_observed)
