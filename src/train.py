import numpy as np
import pudb
import brian2 as br
import weight_updates_numba as weight_updates
import weight_updates_py

br.prefs.codegen.target = 'weave'  # use the Python fallback
def resume_supervised_update_setup(self, hidden=True):
    #pudb.set_trace()
    a = self.net['input']
    ii, ti = self.indices, self.times
    ih, th = self.net['crossings_h'].it_
    ia, ta = self.net['crossings_o'].it_
    d = self.desired

    #print "\t", ta
    #print "\t", ia
    a = self.net['crossings_o']
    b = self.net['crossings_h']

    actual_s = a.all_values()['t']
    hidden_s = b.all_values()['t']

    #pudb.set_trace()
    m, n, o= self.N_inputs, self.N_hidden, self.N_output
    #Si = self.times
    #Sa, Sd = self.actual, self.desired
    #Sa, Sh = weight_updates.sort(Sa), weight_updates.sort(Sh)
    w_ho = self.net['synapses_output'].w[:]
    w_ih = self.net['synapses_hidden'].w[:]
    dw_ho = np.zeros(np.shape(w_ho), dtype=np.float64)
    dw_ih = np.zeros(np.shape(w_ih), dtype=np.float64)
    tau = self.net['synapses_hidden'].tau1 / (1000*br.msecond)
    dw_o = weight_updates.resume_update_output_weights(\
                dw_ho, m, n, o, ih[:], th[:], ia[:], ta[:], d, tau)
    if hidden == True:
        dw_h = weight_updates.resume_update_hidden_weights(\
                    dw_ih, w_ho, m, n, o, ii, ti/br.second, \
                    ih[:], th[:], ia[:], ta[:], d, tau)
        return dw_o, dw_h
    return dw_o
    #dw_o_py = weight_updates_py.resume_update_output_weights(self)
    #dw_h_py = weight_updates_py.resume_update_hidden_weights(self)

    #ocmp = np.allclose(dw_h, dw_h_py, rtol=4*(1e-2), atol=3e-1)
    #hcmp = np.allclose(dw_o, dw_o_py, rtol=4*(1e-2), atol=3e-1)
    #if not ocmp or not hcmp:
    #    pudb.set_trace()


    #print "\tDIFFS:"
    #print "\t\tout:\t", dw_o - dw_o_py
    #print "\t\thidden:\t", dw_h - dw_h_py
    #pudb.set_trace()

def supervised_update(self, iteration, display=False, method='resume', hidden=True):
    #if iteration == 3:
    #    pudb.set_trace()
    if hidden == True:
        dw_o, dw_h = resume_supervised_update_setup(self, hidden=hidden)
        self.actual = self.net['crossings_o'].all_values()['t']
        self.net.restore()
        self.net['synapses_output'].w += self.r*dw_o[:]
        self.net['synapses_hidden'].w += self.r*dw_h[:]
        w_o = self.net['synapses_output'].w
        w_h = self.net['synapses_output'].w
        self.net.store()
    else:
        dw_o = resume_supervised_update_setup(self, hidden=hidden)
        self.actual = self.net['crossings_o'].all_values()['t']
        self.net.restore()
        self.net['synapses_output'].w += self.r*dw_o[:]
        w_o = self.net['synapses_output'].w
        w_h = self.net['synapses_output'].w
        self.net.store()

def synaptic_scaling_step(w, m, n, tomod, spikes):
    f = 0.20
    ### m neuron layer to n neuron layer
    ### w[n*i + j] acceses the synapse from neuron i to neuron j

    mod = False
    for j in tomod:
        #if len(spikes[j]) > 3:
        #    w[j:m*n:n] *= 1 - f
        if len(spikes[j]) == 0:
            w[j:m*n:n] *= 1 + f

def print_times(self):
    a = self.net['crossings_o']
    b = self.net['crossings_h']

    actual = a.all_values()['t']
    hidden = b.all_values()['t']
    
    print "\n\t\t[", hidden, "]\n\t\t[", actual, "]\n"

def synaptic_scaling(self):
    w_ih = self.net['synapses_hidden'].w
    w_ho = self.net['synapses_output'].w

    a = self.net['crossings_o']
    b = self.net['crossings_h']

    actual = a.all_values()['t']
    hidden = b.all_values()['t']

    #print "\n\t\t[", hidden, "]\n\t\t[", actual, "]\n"
    tomod_a = [i for i in actual if len(actual[i]) == 0 or len(actual[i]) > 3]
    tomod_h = [i for i in hidden if len(hidden[i]) == 0 or len(actual[i]) > 3]
    if tomod_a != [] or tomod_h != []:
        self.net.restore()
        synaptic_scaling_step(w_ih, self.N_inputs, self.N_hidden, tomod_h, hidden)
        synaptic_scaling_step(w_ho, self.N_hidden, self.N_output, tomod_a, actual)
        self.net.store()
        return True
    return False

def train_step(self, iteration, T=None, method='resume', hidden=True):
    mod = True
    i = 1
    while mod:
        self.run(T)
        #print "\t run_try", i,
        if i == 70:
            pudb.set_trace()
        #print_times(self)
        mod = synaptic_scaling(self)
        i += 1

    #print "\t train",
    #print_times(self)
    supervised_update(self, iteration, method=method, hidden=hidden)
    #self.actual = self.net['crossings_o'].all_values()
    #self.save_weights()
    #pudb.set_trace()
    #self.run(T)

def train_epoch(self, iteration, images, method='resume', hidden=True):
    correct = 0
    #i, j = a, 0
    p = 0
    for i in images:
        #for i in range(a, b):
        label = self.read_image(i)
        #if label == 0:
        #j += 1
        train_step(self, iteration, method=method, hidden=hidden)
        p += self.performance()
        if self.neuron_right_outputs(label):
            print "*",
            correct += 1
        else:
            print "-",
    print " ",
    return len(images), correct, p
