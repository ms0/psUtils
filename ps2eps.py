"""Python script to create foo.eps from single-page foo.ps, using ghostscript
Usage: ps2eps foo"""

from sys import argv
from subprocess import *

MAXCPL = 80 # max number of characters per line (EPS 3.0 says 255)
# We'll prefix each line of hexits with '% ' and end with '\n'.
# Then limit number of hexits to 72 (4 inches @ 72dpi):
MAXBPL = 36;    # maximum number of bytes per line

def B2i(b) :
  """Convert bytes in big-endian order to int"""
  n = 0;
  for c in b :
    n = (n<<8)|c;
  return n;

def b2i(b) :
  """Convert bytes in little-endian order to int"""
  return B2i(b[::-1])

def main(filename) :
  """Given a filename (without the extension) of a single-page PS file,
  turn filename.ps into an eps with bmpmono preview using gs to produce a
  bounding box and then a bmpmono file.
  First, filename.bps is created that includes the %%BoundingBox comment;
  then, filename.eps is created that includes the preview."""
  cp = run(['gs','-q','-sDEVICE=bbox',filename+'.ps','-'],input=bytes('\nshowpage\n','utf-8'),stderr=PIPE);
  bb = cp.stderr.decode('utf-8').split('\n')[0];
  with open(filename+'.ps','r') as fin :
    with open(filename+'.bps','w') as fout :
      fout.write('%!PS-Adobe-3.0 EPSF-3.0\n')
      fout.write(bb+'\n')
      fout.write('%%Pages: 1\n')
      fout.write('%%EndComments\n')
      fout.write('%%Page: 1 1\n')
      fout.write(fin.read())
      fout.write('\n%%EOF\n')
  cp = run(['gs','-q','-dEPSCrop','-sDEVICE=bmpmono','-sOutputFile=-',filename+'.bps','-'],input=bytes('\nshowpage\n','utf-8'),stdout=PIPE);
  bm = cp.stdout;
  off = b2i(bm[10:14])
  width = b2i(bm[18:22])
  height = b2i(bm[22:26])
  bc = (width+7)//8    # byte count per scanline
  bpl = min(MAXBPL,(width+7)//8)    # bytes per line
  bil = bpl*8    # bits in line
  lps = (width+bil-1)//bil    # lines per scanline
  dx = (width+31)//32*4;    # input bytes per line
  xb = dx-bc;    # excess bytes in bm line
  with open(filename+'.bps','r') as fin :
    with open(filename+'.eps','w') as fout :
      while 1 :
        s = fin.readline();
        fout.write(s);
        if s.rstrip() == '%%EndComments' : break;
      fout.write('%%BeginPreview:')
      fout.write('%d %d 1 %d\n'%(width,height,height*lps));
      bm = bm[off:];
      for l in range(dx*height-xb,0,-dx) :
        line = bm[l-bc:l];
        for c in range(lps) :
          fout.write(('%% %0'+str(2*min(bpl,bc-c*bpl))+'X\n')%(
            B2i(line[c*bpl:(c+1)*bpl])))
      fout.write('%%EndPreview\n')
      fout.write(fin.read())

if __name__=='__main__' :
  main(argv[1]);
