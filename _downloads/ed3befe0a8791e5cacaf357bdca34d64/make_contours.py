"""
=====================
Design biplanar coils
=====================

Example demonstrating how to create biplanar coils for production.
"""

# Authors: Mainak Jas <mjas@mgh.harvard.edu>
#          Padma Sundaram <padma@nmr.mgh.harvard.edu>

# First, we will import the necessary libraries
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from bfieldtools.utils import load_example_mesh
import pyvista as pv

import opm_coils
from opm_coils import BiplanarCoil, get_sphere_points, get_target_field

N_suh = 50
N_contours = 30

center = np.array([0, 0, 0])
target_type = 'dc_y'  # 'gradient_x' | 'gradient_y' | 'dc_x' | 'dc_y' | 'dc_grad_x' etc.

# %%
# Next we define the output directory containing the kicad files for our
# PCB design. 

pcb_dir = Path(opm_coils.__path__[0]).parents[0]

output_dir = {'dc_x': 'Bx_coil',
              'dc_y': 'By_coil',
              'dc_z': 'Bz_coil',
              'gradient_x': 'Gx_coil',
              'gradient_y': 'Gy_coil',
              'gradient_z': 'Gz_coil'}
header_type = {'dc_x': 'vert',
               'dc_y': 'horz',
               'dc_z': 'vert',
               'gradient_x': 'vert',
               'gradient_y': 'horz',
               'gradient_z': 'vert'}
bounds_wholeloop = {'dc_x': False,
                    'dc_y': True,
                    'dc_z': False, 
                    'gradient_x': False,
                    'gradient_y': True,
                    'gradient_z': False}

pcb_fname = pcb_dir / 'development' / output_dir[target_type] / 'first' / 'coil_template_first.kicad_pcb'
kicad_header = pcb_dir / 'kicad' / 'headers' / f'kicad_header_{header_type[target_type]}_first_half.txt'

# %%
# Next we will define the parameters of our coils

trace_width = 5. # mm
cu_oz = 2. # oz per ft^2

# %%
# A 10 m x 10 m biplanar coil mesh is loaded from bfieldtools.
# We will scale the mesh so as to achieve the dimensions of
# 1.4 m x 1.4 m that we will use in our work.

scaling_factor = 0.14
standoff = scaling_factor * 10

planemesh = load_example_mesh("10x10_plane_hires")
planemesh.apply_scale(scaling_factor)

# %%
# The BiplanarCoil class is instantiated
coil = BiplanarCoil(planemesh, center, N_suh=N_suh, standoff=standoff)

# %%
# Then the target points and the fields are used to fit the coil design
target_points, points_z = get_sphere_points(center, n=8, sidelength=0.5)
target_field = get_target_field(target_type, target_points)

coil.fit(target_points, target_field)

# %%
# We discretize the optimized stream function
coil.discretize(N_contours=N_contours, trace_width=trace_width, cu_oz=cu_oz)

# %%
# We plot both the optimized continuous stream function and it's discretized
# counterpart. The camera position is 'xy' for optimal viewing
plotter = pv.Plotter(window_size=(1500, 1700))
coil.coil_.s.plot(figure=plotter)
plotter.camera_position = 'xy'

coil.loops_ = [loop for loop in coil.loops_ if loop[0, 2] > 0]  # just one coil
plotter = coil.plot_field(target_points)
plotter.camera_position = 'xy'

# %%
# We can evaluate the coil for metrics such as efficiency
metrics = coil.evaluate(target_type, target_points, target_field,
                        points_z, 'all')
print(metrics)

# %%
# Next, we make cuts using the interactive interface

# %%
# coil.make_cuts()
coil.save(pcb_fname=pcb_fname, kicad_header_fname=kicad_header,
          bounds=(0,750,0,1500), origin= (0, 750),
          bounds_wholeloop=bounds_wholeloop[target_type])
