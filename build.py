#!/usr/bin/env python3
"""
Generates one static page per conversion pair from index.html.
Run:  python3 build.py
Output: pages/<from>-to-<to>.html
"""
import re, os, html

SRC = 'index.html'
OUT = 'pages'

# ── format facts, used to build unique copy per page ──
F = {
 'PNG':  dict(name='PNG', full='Portable Network Graphics', ext='png',
              lossy=False, alpha=True, key='JPG',
              what='PNG is a lossless format, which means every pixel is preserved exactly as it was. It also supports transparency, so it is the usual choice for logos, icons, screenshots and any graphic with sharp edges or text.',
              weak='Because nothing is thrown away, PNG files of photographs are often several times larger than the same image as JPG or WebP.'),
 'JPG':  dict(name='JPG', full='Joint Photographic Experts Group', ext='jpg',
              lossy=True, alpha=False, key='PNG',
              what='JPG is the most widely supported image format in existence. It uses lossy compression, discarding detail the eye is unlikely to notice in order to produce a much smaller file.',
              weak='JPG cannot store transparency, and repeatedly re-saving a JPG degrades it a little each time.'),
 'JPEG': dict(name='JPEG', full='Joint Photographic Experts Group', ext='jpeg',
              lossy=True, alpha=False, key='PNG',
              what='JPEG is the same format as JPG. The two spellings exist only because older systems limited file extensions to three characters.',
              weak='JPEG cannot store transparency, and each re-save loses a little quality.'),
 'WEBP': dict(name='WebP', full='Web Picture format', ext='webp',
              lossy=True, alpha=True, key='JPG',
              what='WebP was built by Google specifically for the web. It can compress either lossily or losslessly, supports transparency, and is typically 25 to 35 percent smaller than JPG at matching visual quality.',
              weak='Some older desktop software and a few printing services still do not accept WebP.'),
 'AVIF': dict(name='AVIF', full='AV1 Image File Format', ext='avif',
              lossy=True, alpha=True, key='JPG',
              what='AVIF is the newest of the mainstream web formats. It generally produces the smallest file of any of them at a given quality, supports transparency, and handles gradients and flat colour especially well.',
              weak='Support outside browsers is still patchy, and not every browser can create AVIF files even though nearly all can display them.'),
 'GIF':  dict(name='GIF', full='Graphics Interchange Format', ext='gif',
              lossy=False, alpha=True, key='PNG',
              what='GIF stores a maximum of 256 colours per image and supports simple animation. It is the oldest format still in common use on the web.',
              weak='The 256-colour limit makes GIF a poor choice for photographs, which end up visibly banded. For still images PNG is almost always better.'),
 'BMP':  dict(name='BMP', full='Bitmap', ext='bmp',
              lossy=False, alpha=False, key='PNG',
              what='BMP stores pixels with no compression at all. That makes it simple and completely lossless, and it is still used by some Windows software and older imaging tools.',
              weak='Files are very large — often ten times the size of the same image as PNG — and it has no place on a modern website.'),
 'TIFF': dict(name='TIFF', full='Tagged Image File Format', ext='tiff',
              lossy=False, alpha=True, key='PNG',
              what='TIFF is the standard in printing, publishing and archiving. It is lossless, supports very high bit depths, and can carry multiple pages in a single file.',
              weak='Browsers cannot display TIFF, and the files are large, so it is unsuitable for the web.'),
 'ICO':  dict(name='ICO', full='Icon', ext='ico',
              lossy=False, alpha=True, key='PNG',
              what='ICO is the container Windows and web browsers use for icons. A favicon — the small image beside a page title in a browser tab — is normally an ICO file.',
              weak='It is only meant for small square icons and has no use as a general image format.'),
 'PDF':  dict(name='PDF', full='Portable Document Format', ext='pdf',
              lossy=True, alpha=False, key='JPG',
              what='PDF is a document format rather than an image format. It keeps its layout identically on every device, which is why it is the standard for anything that will be printed, emailed or filed.',
              weak='A PDF is heavier than a plain image and cannot be edited as easily.'),
 'HEIC': dict(name='HEIC', full='High Efficiency Image Container', ext='heic',
              lossy=True, alpha=True, key='JPG',
              what='HEIC is the format an iPhone uses by default. It stores roughly the same quality as JPG in about half the space.',
              weak='Outside the Apple ecosystem support is poor, which is why HEIC photos so often need converting before they can be shared or uploaded.'),
}

PAIRS = [
 ('PNG','JPG'), ('JPG','PNG'), ('PNG','WEBP'), ('JPG','WEBP'),
 ('WEBP','PNG'), ('WEBP','JPG'), ('HEIC','JPG'), ('PNG','AVIF'),
 ('JPG','AVIF'), ('AVIF','JPG'), ('GIF','PNG'), ('PNG','GIF'),
 ('BMP','JPG'), ('JPG','BMP'), ('PNG','ICO'), ('JPG','ICO'),
 ('PNG','TIFF'), ('TIFF','JPG'), ('JPG','PDF'), ('PNG','PDF'),
 ('WEBP','PDF'), ('GIF','JPG'), ('AVIF','PNG'), ('HEIC','PNG'),
]

DOMAIN = 'https://mytoolsbench.vercel.app'


def slug(a, b):
    return f"{F[a]['ext']}-to-{F[b]['ext']}"


def why(a, b):
    """One or two sentences on why someone makes this specific conversion."""
    A, B = F[a], F[b]
    if B['name'] == 'PDF':
        return (f"Turning a {A['name']} into a PDF is the usual step before emailing, printing or filing an image, "
                f"because a PDF opens the same way on every device and is accepted by forms and portals that reject raw images.")
    if B['name'] == 'ICO':
        return (f"ICO is what browsers and Windows expect for icons, so converting a {A['name']} to ICO is normally "
                f"the last step before adding a favicon to a website or an icon to a desktop application.")
    if A['name'] == 'HEIC':
        return (f"HEIC is what your iPhone saves photos as, and almost nothing outside Apple's ecosystem will open it. "
                f"Converting to {B['name']} makes the photo usable everywhere — email, websites, Windows, print shops.")
    if A['lossy'] is False and B['lossy'] is True and A['name'] != 'GIF':
        return (f"{A['name']} keeps every pixel, which makes it large. Converting to {B['name']} trades a small amount of "
                f"detail for a much smaller file, which is usually the right choice for photographs and anything going on a website.")
    if A['lossy'] and not B['lossy']:
        return (f"Converting {A['name']} to {B['name']} stops any further quality loss and gives you a file that supports "
                f"transparency, which is useful if you plan to edit the image or place it over a coloured background.")
    if B['name'] in ('WEBP', 'AVIF'):
        return (f"{B['name']} is built for the web and is typically far smaller than {A['name']} at the same visual quality, "
                f"so this conversion is one of the quickest ways to make a page load faster without visibly changing the images.")
    if A['name'] == 'GIF':
        return (f"GIF is limited to 256 colours, so still images stored as GIF often look banded. Converting to "
                f"{B['name']} restores the full colour range and usually produces a smaller file too.")
    if A['name'] == 'BMP':
        return (f"BMP files are uncompressed and enormous. Converting to {B['name']} typically cuts the size by "
                f"90 percent or more with no visible difference.")
    if A['name'] == 'TIFF':
        return (f"TIFF is a print and archive format that browsers cannot display. Converting to {B['name']} makes the "
                f"image usable on the web and shrinks it considerably.")
    return (f"Converting {A['name']} to {B['name']} makes the image easier to share and use in places that expect "
            f"{B['name']} files.")


def faqs(a, b):
    A, B = F[a], F[b]
    out = []
    if A['alpha'] and not B['alpha']:
        out.append((f"Will I lose transparency converting {A['name']} to {B['name']}?",
                    f"Yes — {B['name']} cannot store transparent pixels, so any transparent area has to be filled with a solid colour. "
                    f"This tool fills with white, which is what most people expect. Many converters fill with black and leave you with dark edges. "
                    f"If you need to keep transparency, convert to PNG, WebP or AVIF instead."))
    if not A['lossy'] and B['lossy']:
        out.append((f"Does converting {A['name']} to {B['name']} reduce quality?",
                    f"Slightly, by design. {B['name']} uses lossy compression to make the file smaller. At the default quality of 85 "
                    f"the difference is invisible on most images. Raise the quality slider if you are working with fine detail, "
                    f"text or flat colour."))
    if A['lossy'] and not B['lossy']:
        out.append((f"Will converting {A['name']} to {B['name']} improve the quality?",
                    f"No. Detail already discarded by {A['name']} cannot be recovered. What converting to {B['name']} does is stop "
                    f"any further loss, so the image will not degrade again on the next save."))
    out.append((f"Is there a limit on file size or how many files I can convert?",
                f"No. Conversion runs inside your browser rather than on a server, so there is no upload, no queue and no cap. "
                f"Very large images may simply take a moment on a slower device."))
    out.append((f"Are my {A['name']} files uploaded anywhere?",
                f"No. Your files are read and written by your own browser and never leave your device. You can disconnect from "
                f"the internet once the page has loaded and the converter will still work."))
    if A['name'] == 'HEIC':
        out.append(("Do I need Safari or an iPhone to convert HEIC?",
                    "No. HEIC files are decoded here in any modern browser, including Chrome, Firefox and Edge on Windows. "
                    "You will see a brief 'decoding HEIC' message while each file is read, then it converts like any other image."))
        out.append(("Why are my iPhone photos saved as HEIC?",
                    "Apple switched to HEIC because it stores roughly the same quality as JPG in about half the space. The "
                    "trade-off is that most non-Apple software cannot open it, which is why converting to JPG or PNG is so common."))
    if B['name'] == 'JPEG' or A['name'] == 'JPEG':
        out.append(("Is JPEG the same as JPG?",
                    "Yes, completely. The two spellings exist only because older systems limited file extensions to three characters."))
    return out


def build_page(src, a, b):
    A, B = F[a], F[b]
    s = slug(a, b)
    title = f"{A['name']} to {B['name']} Converter — Free, No Upload"
    desc = (f"Convert {A['name']} to {B['name']} online for free. Batch conversion, no file size limit, no sign-up. "
            f"Files are processed in your browser and never uploaded.")

    doc = src

    # head
    doc = re.sub(r'<title>.*?</title>', f'<title>{html.escape(title)}</title>', doc, count=1, flags=re.S)
    doc = re.sub(r'(<meta name="description" content=")[^"]*(">)',
                 lambda m: m.group(1) + html.escape(desc) + m.group(2), doc, count=1)
    doc = re.sub(r'(<link rel="canonical" href=")[^"]*(">)',
                 lambda m: m.group(1) + f'{DOMAIN}/{s}' + m.group(2), doc, count=1)

    # hero
    hero_new = (f'    <h1>{A["name"]} to {B["name"]} Converter</h1>\n'
                f'    <p>Convert {A["name"]} images to {B["name"]}, for free. '
                f'Files are processed in your browser and never uploaded.</p>')
    doc = re.sub(r'    <h1>Image Converter</h1>\n    <p>.*?</p>', hero_new, doc, count=1, flags=re.S)

    # default output format in JS
    doc = doc.replace("out:'JPG',quality:85,maxw:0,", f"out:'{B['name']}',quality:85,maxw:0,")

    # how-to steps, format specific
    doc = doc.replace(
        '<li>Click the <b>Choose Files</b> button and select the images you want to convert.</li>',
        f'<li>Click the <b>Choose Files</b> button and select your {A["name"]} files.</li>')
    doc = doc.replace(
        '<li>Set the <b>Output</b> format for each file, then click the gear if you want to adjust quality or size.</li>',
        f'<li>{B["name"]} is already selected as the output. Click the gear if you want to adjust quality or resize.</li>')
    doc = doc.replace(
        '<li>Click <b>Convert</b>, then hit <b>Download</b> on each file or grab everything as a ZIP.</li>',
        f'<li>Click <b>Convert</b>, then hit <b>Download</b> to save your {B["name"]} files, or grab them all as a ZIP.</li>')

    # "how to use" heading
    doc = doc.replace('<h2 class="sh">How to use this image converter</h2>',
                      f'<h2 class="sh">How to convert {A["name"]} to {B["name"]}</h2>')

    # why-convert block inserted before the how-to list
    whyblock = (f'    <p class="lead">{html.escape(why(a, b))}</p>\n'
                f'    <ol class="howto">')
    doc = doc.replace('    <ol class="howto">', whyblock, 1)

    # feature column 1 rewritten per pair
    doc = re.sub(
        r'<h3>Convert any image</h3>\s*<p>.*?</p>',
        f'<h3>Built for {A["name"]} files</h3>\n        <p>Drop in as many {A["name"]} images as you like and they all '
        f'come out as {B["name"]}. You can also change the output on any individual file if you need a mixed batch.</p>',
        doc, count=1, flags=re.S)

    # "what is a format" accordion -> pair specific
    fmt_acc = (
        f'    <details class="acc">\n'
        f'    <summary><span>What is a {A["name"]} file?</span></summary>\n'
        f'    <div class="acc-body">\n'
        f'      <p><b>{A["name"]}</b> stands for {A["full"]}. {A["what"]}</p>\n'
        f'      <p>{A["weak"]}</p>\n'
        f'    </div>\n'
        f'  </details>\n\n'
        f'  <details class="acc">\n'
        f'    <summary><span>What is a {B["name"]} file?</span></summary>\n'
        f'    <div class="acc-body">\n'
        f'      <p><b>{B["name"]}</b> stands for {B["full"]}. {B["what"]}</p>\n'
        f'      <p>{B["weak"]}</p>\n'
        f'    </div>\n'
        f'  </details>'
    )
    doc = re.sub(
        r'  <details class="acc">\s*<summary><span>What is an image file format\?</span></summary>.*?</details>',
        fmt_acc, doc, count=1, flags=re.S)

    # FAQ block
    faq_html = '\n'.join(
        f'    <details class="faq"><summary>{html.escape(q)}</summary>\n      <p>{html.escape(ans)}</p></details>'
        for q, ans in faqs(a, b))
    doc = re.sub(
        r'(<h2 class="sh">Frequently asked questions</h2>\n).*?(\n  </section>)',
        lambda m: m.group(1) + faq_html + m.group(2), doc, count=1, flags=re.S)

    # link grid: drop self-link, point home
    doc = doc.replace(f'<a href="/{s}">', '<a class="cur" href="#">')
    doc = doc.replace('<a href="/" class="logo">', '<a href="/" class="logo">')

    # breadcrumb-ish back link in nav
    doc = doc.replace('<a href="#how">How it works</a>',
                      '<a href="/">All formats</a>')

    # lead paragraph style + current-link style
    doc = doc.replace('</style>',
                      '.lead{font-size:.95rem;color:var(--ink-2);margin-bottom:18px;max-width:660px}\n'
                      '.pairs a.cur{color:var(--ink-3);font-weight:700;pointer-events:none}\n</style>')

    # structured data
    ld = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"HowTo",'
        f'"name":"How to convert {A["name"]} to {B["name"]}",'
        '"step":['
        f'{{"@type":"HowToStep","text":"Select your {A["name"]} files."}},'
        f'{{"@type":"HowToStep","text":"{B["name"]} is preselected as the output format."}},'
        f'{{"@type":"HowToStep","text":"Click Convert and download your {B["name"]} files."}}'
        ']}</script>\n</head>'
    )
    doc = doc.replace('</head>', ld, 1)

    return doc


def main():
    src = open(SRC, encoding='utf-8').read()
    os.makedirs(OUT, exist_ok=True)
    made = []
    for a, b in PAIRS:
        page = build_page(src, a, b)
        path = os.path.join(OUT, slug(a, b) + '.html')
        open(path, 'w', encoding='utf-8').write(page)
        made.append((slug(a, b), len(page)))
    for s, n in made:
        print(f'  {s:<18} {n:,} bytes')
    print(f'\n{len(made)} pages written to {OUT}/')


if __name__ == '__main__':
    main()
