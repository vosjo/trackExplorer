
import os
import h5py

import numpy as np

from numpy.lib.recfunctions import append_fields

from scipy.interpolate import interp1d

def read_hdf5(filename):
    """
    Read the filestructure of a hdf5 file to a dictionary.

    @param filename: the name of the hdf5 file to read
    @type filename: str
    @return: dictionary with read filestructure
    @rtype: dict
    """

    if not os.path.isfile(filename):
        print("File does not exist")
        raise IOError

    def read_rec(hdf):
        """ recursively read the hdf5 file """
        res = {}
        for name, grp in hdf.items():
            # -- read the subgroups and datasets
            if hasattr(grp, 'items'):
                # in case of a group, read the group into a new dictionary key
                res[name] = read_rec(grp)
            else:
                # in case of dataset, read the value
                res[name] = grp.value

        # -- read all the attributes
        for name, atr in hdf.attrs.items():
            res[name] = atr

        return res

    hdf = h5py.File(filename, 'r')
    result = read_rec(hdf)
    hdf.close()

    return result


def read_history(objectname, return_profiles=False):

    data_ = read_hdf5(objectname)

    history = data_.pop('history', None)
    d1 = history.pop('star1', None)
    d2 = history.pop('star2', None)
    db = history.pop('binary', None)


    extra_info = data_.pop('extra_info', None)

    # set model number for primary to start at 1 and limits to correct last model number
    d1['model_number'] = d1['model_number'] - d1['model_number'][0] + 1
    s = np.where(db['model_number'] <= d1['model_number'][-1])
    db = db[s]

    # PRIMARY
    # now interpolate primary data to match model numbers for binary history
    dtypes = d1.dtype
    y = d1.view(np.float64).reshape(-1, len(dtypes))
    f = interp1d(d1['model_number'], y, axis=0, bounds_error=False, fill_value=0.0)
    d1 = f(db['model_number'])

    # reconvert from array to recarray
    d1 = [tuple(d) for d in d1]
    d1 = np.array(d1, dtype=dtypes)

    # remove model_number as column from d1 and merge into 1 recarray
    columns1 = list(d1.dtype.names)
    columns1.remove('model_number')
    column_names1 = [c for c in columns1]

    # SECONDARY
    # now interpolate secondary data to match model numbers for binary history
    dtypes = d2.dtype
    y = d2.view(np.float64).reshape(-1, len(dtypes))
    f = interp1d(d2['model_number'], y, axis=0, bounds_error=False, fill_value=0.0)
    d2 = f(db['model_number'])

    # reconvert from array to recarray
    d2 = [tuple(d) for d in d2]
    d2 = np.array(d2, dtype=dtypes)

    # remove model_number as column from d1 and merge into 1 recarray
    columns2 = list(d2.dtype.names)
    columns2.remove('model_number')
    column_names2 = [c+'_2' for c in columns2]

    # create a new record array from the data (much faster than appending to an existing array)
    columnsdb = list(db.dtype.names)
    data = np.core.records.fromarrays \
        ([db[c] for c in columnsdb] + [d1[c] for c in columns1] + [d2[c] for c in columns2],
                                      names=columnsdb + column_names1 + column_names2)

    if not 'effective_T' in data.dtype.names:
        data = append_fields(data, ['effective_T'], [10**data['log_Teff']], usemask=False)

    if not 'effective_T_2' in data.dtype.names:
        data = append_fields(data, ['effective_T_2'], [10**data['log_Teff_2']], usemask=False)

    if not 'rl_overflow_1' in data.dtype.names:
        data = append_fields(data, ['rl_overflow_1'], [data['star_1_radius'] / data['rl_1']], usemask=False)

    if not 'mass_ratio' in data.dtype.names:
        data = append_fields(data, ['mass_ratio'], [data['star_1_mass'] / data['star_2_mass']], usemask=False)

    if not 'separation_au' in data.dtype.names:
        data = append_fields(data, ['separation_au'], [data['binary_separation'] * 0.004649183820234682], usemask=False)

    J_Jdot_P = (data['J_orb'] / np.abs(data['Jdot'])) / (data['period_days'] * 24.0 *60.0 *60.0)
    J_Jdot_P = np.where((J_Jdot_P == 0 ), 99, np.log10(J_Jdot_P))
    data = append_fields(data, ['log10_J_div_Jdot_div_P'], [J_Jdot_P], usemask=False)

    M_Mdot_P = (data['star_1_mass'] / 10 ** data['lg_mstar_dot_1']) / (data['period_days'] / 360)
    M_Mdot_P = np.where((M_Mdot_P == 0), 99, np.log10(M_Mdot_P))
    data = append_fields(data, ['log10_M_div_Mdot_div_P'], [M_Mdot_P], usemask=False)

    data = append_fields(data, ['R1_div_a'], [data['star_1_radius'] / data['binary_separation']], usemask=False)

    if return_profiles:
        if 'profiles' not in data_:
            profiles = None
        else:
            profiles = data_.get('profiles')
            profiles['legend'] = data_.get('profile_legend')

        return data, profiles

    return data
