from __future__ import division
import tkFont
import Tkinter as Tk
from time import time

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,\
    NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import numpy
import sqlitedict

#####################
# User-set parameters
#####################

db_name = 'aerostruct.db'
show_wing = True
show_tube = True
initial_iteration = 0

def _get_lengths(self, A, B, axis):
    return numpy.sqrt(numpy.sum((B - A)**2, axis=axis))

class Display(object):
    def __init__(self, db_name, show_wing, show_tube, initial_iteration):
        self.s = time()
        self.root = Tk.Tk()

        self.f = plt.figure(dpi=100, figsize=(12, 6), facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.f, master=self.root)
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        self.options_frame = Tk.Frame(self.root)
        self.options_frame.pack()

        self.canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.ax = plt.subplot2grid((4,8), (0,0), rowspan=4, colspan=4, projection='3d')

        if show_wing and not show_tube:
            self.ax2 = plt.subplot2grid((4,8), (0,4), rowspan=2, colspan=4)
            self.ax3 = plt.subplot2grid((4,8), (2,4), rowspan=2, colspan=4)
        if show_tube and not show_wing:
            self.ax4 = plt.subplot2grid((4,8), (0,4), rowspan=2, colspan=4)
            self.ax5 = plt.subplot2grid((4,8), (2,4), rowspan=2, colspan=4)
        if show_wing and show_tube:
            self.ax2 = plt.subplot2grid((4,8), (0,4), colspan=4)
            self.ax3 = plt.subplot2grid((4,8), (1,4), colspan=4)
            self.ax4 = plt.subplot2grid((4,8), (2,4), colspan=4)
            self.ax5 = plt.subplot2grid((4,8), (3,4), colspan=4)

        self.num_iters = 0
        self.db_name = db_name
        self.show_wing = show_wing
        self.show_tube = show_tube
        self.curr_pos = initial_iteration

    def load_db(self):
        self.db = sqlitedict.SqliteDict(self.db_name, 'openmdao')
        self.cl = []
        self.cd = []
        self.twist = []
        self.mesh = []
        self.r = []
        self.t = []
        sec_forces = []
        normals = []
        cos_dih = []
        self.lift = []
        self.vonmises = []

        for case_name, case_data in self.db.iteritems():
            if "metadata" in case_name or "derivs" in case_name:
                continue # don't plot these cases

            self.mesh.append(case_data['Unknowns']['mesh'])
            try:
                self.r.append(case_data['Unknowns']['r'])
                self.t.append(case_data['Unknowns']['t'])
                self.vonmises.append(case_data['Unknowns']['vonmises'])
            except:
                pass
            try:
                self.twist.append(case_data['Unknowns']['twist'])
                normals.append(case_data['Unknowns']['normals'])
                cos_dih.append(case_data['Unknowns']['cos_dih'])
                sec_forces.append(case_data['Unknowns']['sec_forces'])
            except:
                pass

        if self.show_wing:
            for i in range(len(sec_forces)):
                L = sec_forces[i][:, 2] / normals[i][:, 2]
                self.lift.append(L.T * cos_dih[i])
        self.num_iters = len(self.mesh) - 1

    def plot_sides(self):
        m_vals = self.mesh[self.curr_pos]
        span = (m_vals[0, :, 1] / (m_vals[0, -1, 1]) - 0.5) * 2
        span_diff = ((m_vals[0, :-1, 1] + m_vals[0, 1:, 1])/2 / (m_vals[0, -1, 1]) - 0.5) * 2

        if self.show_tube:
            thick_vals = self.t[self.curr_pos]
            vm_vals = self.vonmises[self.curr_pos]

            self.ax4.plot(span_diff, thick_vals, lw=2, c='b')
            self.ax4.locator_params(axis='y',nbins=3)
            self.ax4.locator_params(axis='x',nbins=3)
            self.ax4.set_ylabel('thickness', rotation="horizontal", ha="right")

            self.ax5.plot(span_diff, vm_vals, lw=2, c='b')
            self.ax5.locator_params(axis='y',nbins=3)
            self.ax5.locator_params(axis='x',nbins=3)
            self.ax5.set_ylabel('von mises', rotation="horizontal", ha="right")

        if self.show_wing:
            t_vals = self.twist[self.curr_pos]
            l_vals = self.lift[self.curr_pos]

            self.ax2.plot(span, t_vals, lw=2, c='b')
            self.ax2.locator_params(axis='y',nbins=3)
            self.ax2.locator_params(axis='x',nbins=3)
            self.ax2.set_ylabel('twist', rotation="horizontal", ha="right")

            self.ax3.plot(span_diff, l_vals, lw=2, c='b')
            self.ax3.locator_params(axis='y',nbins=3)
            self.ax3.locator_params(axis='x',nbins=3)
            self.ax3.set_ylabel('lift', rotation="horizontal", ha="right")

    def plot_wing(self):
        az = self.ax.azim
        el = self.ax.elev
        dist = self.ax.dist
        mesh0 = self.mesh[self.curr_pos]
        self.ax.set_axis_off()

        x = mesh0[:, :, 0]
        y = mesh0[:, :, 1]
        z = mesh0[:, :, 2]
        if self.show_wing:
            self.ax.plot_wireframe(x, y, z, rstride=1, cstride=1, color='k')

        # TODO: will need to account for 3d geometry here
        if self.show_tube:
            r0 = self.r[self.curr_pos]
            t0 = self.t[self.curr_pos]
            r0 = numpy.hstack((r0, r0[-1]))
            t0 = numpy.hstack((t0, t0[-1]))
            n = mesh0.shape[1]
            num_circ = 12
            fem_origin = 0.35 # TODO: hard-coded, need to take this from the user
            p = numpy.linspace(0, 2*numpy.pi, num_circ)
            R, P = numpy.meshgrid(r0, p)
            X, Z = R*numpy.cos(P), R*numpy.sin(P)
            chords = mesh0[1, :, 0] - mesh0[0, :, 0]
            X[:] += -fem_origin * chords + mesh0[1, :, 0]
            Y = numpy.empty(X.shape)
            Y[:] = numpy.linspace(0, mesh0[0, -1, 1], n)
            colors = numpy.empty(X.shape)
            colors[:, :] = t0
            colors = colors / numpy.max(colors)
            self.ax.plot_surface(X, Y, Z, rstride=1, cstride=1, facecolors=cm.YlOrRd(colors), linewidth=0, antialiased=False)
        max_dim = numpy.max(numpy.max(mesh0))
        self.ax.auto_scale_xyz([-max_dim/4, max_dim/4], [max_dim/4, 3*max_dim/4], [-max_dim/4, max_dim/4])
        self.ax.set_title("Iteration: {}".format(self.curr_pos))

        self.ax.view_init(elev=el, azim=az) #Reproduce view

    def update_graphs(self, e):
        self.curr_pos = int(e)

        self.curr_pos = self.curr_pos % (self.num_iters + 1)

        self.ax.cla()
        self.plot_wing()

        if self.show_wing:
            self.ax2.cla()
            self.ax3.cla()
        if self.show_tube:
            self.ax4.cla()
            self.ax5.cla()

        self.plot_sides()

        self.canvas.show()


    def quit(self):
        """
        Destroy GUI window cleanly if quit button pressed.
        """
        self.root.quit()
        self.root.destroy()

    def draw_GUI(self):
        """
        Create the frames and widgets in the bottom section of the canvas.
        """
        font = tkFont.Font(family="Helvetica", size=10)

        lab_font = Tk.Label(
            self.options_frame,
            text="Iteration number:",
            font=font)
        lab_font.grid(row=0, column=0, sticky=Tk.S)

        self.w = Tk.Scale(self.options_frame, from_=0, to=self.num_iters, orient=Tk.HORIZONTAL,
                     resolution=1, font=font, command=self.update_graphs, length=200)
        self.w.set(0)
        self.w.grid(row=0, column=1, padx=5, sticky=Tk.W)

if __name__ == '__main__':
    disp = Display(db_name, show_wing=show_wing,
        show_tube=show_tube, initial_iteration=initial_iteration)
    disp.load_db()
    disp.draw_GUI()
    plt.tight_layout()
    disp.root.protocol("WM_DELETE_WINDOW", disp.quit)
    Tk.mainloop()
