"""Read the packaged premultiplied original-stage pixels; never redraw them."""
import numpy as np

class SourceMorph:
    def __init__(self,g):
        with np.load(g.BASELINE/'stages.npz',allow_pickle=False) as data:
            self.rgb=data['rgb'].copy();self.alpha=data['alpha'].copy();self.points=data['points'].copy()
        if self.rgb.shape!=(5,960,720,3) or self.alpha.shape!=(5,960,720):
            raise ValueError('The bundled renderer requires the five-stage seahorse baseline')
        if not np.isfinite(self.rgb).all() or not np.isfinite(self.alpha).all():
            raise ValueError('Invalid endpoint pixels')
