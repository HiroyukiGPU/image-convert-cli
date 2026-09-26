from pathlib import Path
import io
import os
from PIL import Image, ImageOps
from .common import entry, parser, human
COMPRESS=False
FORMATS={'.png':'PNG','.jpg':'JPEG','.jpeg':'JPEG','.webp':'WEBP','.avif':'AVIF'}


def convert(src,dst,quality=80,max_width=None):
    if dst.exists(): raise ValueError(f'出力が既に存在します: {dst}')
    with Image.open(src) as original:
        if getattr(original,'is_animated',False): raise ValueError(f'アニメーション画像は対象外です: {src}')
        img=ImageOps.exif_transpose(original)
        if max_width and img.width>max_width: img.thumbnail((max_width,max(1,round(img.height*max_width/img.width))))
        fmt=FORMATS[dst.suffix.lower()]
        if fmt=='JPEG':
            rgba=img.convert('RGBA'); bg=Image.new('RGB',rgba.size,'white'); bg.paste(rgba,mask=rgba.getchannel('A')); img=bg
        elif img.mode not in ('RGB','RGBA','L','LA','P'): img=img.convert('RGBA')
        buf=io.BytesIO(); options=dict(optimize=True)
        if fmt!='PNG': options['quality']=quality
        img.save(buf,format=fmt,**options)
        result=buf.getvalue()
    # No overwrite, even if another process creates the target during encoding.
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as f: f.write(result)
    return len(result)

@entry
def main():
    p=parser('画像を一括処理。原本は保持します。')
    p.add_argument('input'); p.add_argument('--format',choices=['png','jpg','jpeg','webp','avif'],default=None if COMPRESS else 'webp')
    p.add_argument('--output',default=None); p.add_argument('--quality',type=int,default=80); p.add_argument('--max-width',type=int); p.add_argument('--recursive',action='store_true')
    a=p.parse_args()
    if not 1<=a.quality<=100: p.error('--qualityは1〜100')
    if a.max_width is not None and a.max_width<1: p.error('--max-widthは1以上')
    source=Path(a.input).expanduser().resolve()
    if not source.exists(): raise ValueError('入力がありません')
    root=source if source.is_dir() else source.parent
    out=Path(a.output).expanduser().resolve() if a.output else root/('compressed' if COMPRESS else 'converted')
    candidates=source.rglob('*') if source.is_dir() and a.recursive else source.iterdir() if source.is_dir() else [source]
    files=sorted(f for f in candidates if f.is_file() and not f.is_symlink() and f.suffix.lower() in FORMATS and out not in f.parents)
    if not files: raise ValueError('対応画像がありません')
    jobs=[]
    for file in files:
        dst=(out/file.relative_to(root)).with_suffix('.'+a.format) if a.format else out/file.relative_to(root)
        jobs.append((file,dst))
    if len({str(d).casefold() for _,d in jobs}) != len(jobs): raise ValueError('出力名が重複します。入力を分けてください')
    for _,dst in jobs:
        if dst.exists(): raise ValueError(f'出力が既存です: {dst}')
    for file,dst in jobs:
        before=file.stat().st_size; after=convert(file,dst,a.quality,a.max_width)
        print(f'{file.name} → {dst}  {human(before)} → {human(after)}')
