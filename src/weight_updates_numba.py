import pudb
import numpy as np
#import numba

def sort(S):
    if len(S) > 0:
        for i in range(len(S)):
            S[i] = np.sort(S[i])
    return S

def smaller_indices(a, B):
    indices = []
    for i in range(len(B)):
        if B[i] <= a:
            indices.append(i)
    return np.asarray(indices)

def larger_indices(a, B):
    indices = []
    for i in range(len(B)):
        if B[i] > a:
            indices.append(i)
    return np.asarray(indices)

#@numba.jit(nopython=True)
def resume_kernel(s, tau):
    return np.exp(s/tau)

#@numba.jit(nopython=True)
def resume_update_hidden_weights(dw_ih, w_ho, delay_ih, delay_ho, m, n, o, ii, ti, ih, th, ia, ta, d, tau, Ap, Am, a_nh):
    n_o, m_n_o = n*o, m*n*o
    n_p, o_p = n*p, o*p

    ### m input neurons, n hidden neurons, o output neurons
    ### w_ih[n_p*i + p*j + k] acceses the kth synapse from input i to hidden j
    ### w_ho[o_p*i + p*j + k] acceses the kth synapse from hidden i to output j

    # loop over input neurons
    for I in range(len(ii)):
        i = ii[I]
        # loop over hidden neurons
        for k in range(n):
            # loop over output neurons
            for J in range(len(ta)):
                j = ia[J]
                index_ih = n_p*i+p*k
                index_ho = o_p*k+p*j
                delay = delay_ih[index_ih:index_ih+p]
                s = ta[J] - ti[I] - delay
                if s <= 0:
                    dw_ih[index_ih:index_ih+p] += Am*resume_kernel(s, tau)*np.abs(w_ho[index_ho:index_ho+p])
                if s >= 0 :
                    dw_ih[index_ih:index_ih+p] -= (a_nh + Ap*resume_kernel(-s, tau))*np.abs(w_ho[index_ho:index_ho+p])
            for j in range(len(d)):
                index_ih = n_p*i+p*k
                index_ho = o_p*k+p*j
                delay = delay_ih[index_ih:index_ih+p]
                s = d[j] - ti[I] - delay
                if s <= 0:
                    dw_ih[index_ih:index_ih+p] -= Am*resume_kernel(s, tau)*np.abs(w_ho[index_ho:index_ho+p])
                if s >= 0:
                    dw_ih[index_ih:index_ih+p] += (a_nh + Ap*resume_kernel(-s, tau))*np.abs(w_ho[index_ho:index_ho+p])
    dw_ih /= float(m_n*p*p)
    return dw_ih

#@numba.jit(nopython=True)
def resume_update_output_weights(dw_ho, m, n, o, p, ih, th, ia, ta, d, tau):
    n_o, m_n_o = n*o, m*n*o
    n_p, o_p = n*p, o*p

    ### n hidden neurons, o output neurons, p synapses per neuron/input pair
    ### w_ho[o_p*i + p*j + k] acceses the kth synapses from hidden i to output j

    # loop over hidden spikes
    for I in range(len(ih)):
        i = ih[I]
        # loop over output spikes
        for J in range(len(ia)):
            j = ia[J]
            index_ho = o_p*k+p*j
            delay = delay_ho[index_ho:index_ho+p]
            s = ta[J] - th[I] - delay
            if s <= 0:
                dw_ho[index_ho:index_ho+p] += Am*resume_kernel(s, tau)
            if s >= 0:
                dw_ho[index_ho:index_ho+p] -= a_nh + Ap*resume_kernel(-s, tau)
        # loop over desired spikes
        for j in range(len(d)):
            index_ho = o_p*k+p*j
            delay = delay_ho[index_ho:index_ho+p]
            s = d[j] - th[I] - delay
            if s <= 0:
                dw_ho[index_ho:index_ho+p] -= Am*resume_kernel(s, tau)
            if s >= 0:
                dw_ho[index_ho:index_ho+p] += a_nh + Ap*resume_kernel(-s, tau)
    dw_ho /= float(n_p)
    return dw_ho

def normad_supervised_update_setup(self):
    """ Normad training step """
    #self.actual = self.net['crossings_o'].all_values()['t']
    actual, desired = self.actual, self.desired
    dt = self.dta
    v = self.net['monitor_v'].v
    c = self.net['monitor_o_c'].c
    w = self.net['synapses_output'].w
    #t = self.net['monitor_o'].tp
    #f = self.net['monitor_f'].f
    #a = [max(f[i]) for i in range(len(f))]

    # m neurons, n inputs
    #pudb.set_trace()
    m, n = len(v), len(self.net['synapses_output'].w[:, 0])
    m_n = m*n
    dW, dw = np.zeros(m_n), np.zeros(n)
    for i in range(m):
        if len(actual[i]) > 0:
            index_a = int(actual[i] / dt)
            dw_tmp = c[i:m_n:m, index_a]
            dw_tmp_norm = np.linalg.norm(dw_tmp)
            if dw_tmp_norm > 0:
                dw[:] -= dw_tmp / dw_tmp_norm
        if desired[i] > 0:
            index_d = int(desired[i] / dt)
            dw_tmp = c[i:m_n:m, index_d]
            dw_tmp_norm = np.linalg.norm(dw_tmp)
            if dw_tmp_norm > 0:
                dw[:] += dw_tmp / dw_tmp_norm
        dwn = np.linalg.norm(dw)
        if dwn > 0:
            dW[i:m_n:m] = dw / dwn
        dw *= 0
    return dW
