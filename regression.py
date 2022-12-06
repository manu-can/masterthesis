import os
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.decomposition import _factor_analysis as fa
from scipy import stats

from utils.utils import *


def principal_component_regression(prop):
    # selected 30 street network properties
    cols = ['area', 'length', 'intersection_density_a', 'street_density', 'graph_density', 'mean_node_degree',
            'mean_segment_length', 'deadend_perc', 'mean_deadend_length', 'detour_to_mean_segment_ratio',
            'detour_to_mean_deadend_ratio', 'perc_4_way', 'perc_reg_3_way', 'perc_reg_4_way', 'straightness_perc',
            'area_circularity', 'orientation_order', 'mean_bearing_to_dest', 'mean_cc800', 'mean_cb800', 'mean_cs800',
            'edge_connectivity', 'deadend_start', 'deadend_end', 'cc800_start', 'cc800_end', 'cb800_start', 'cb800_end',
            'cs800_start', 'cs800_end']

    # street network properties (aka features)
    x = prop.loc[:, cols].values

    # correlation of features
    correlation_matrix = prop[cols].corr()
    if city == '01_Vienna' and size == 'big':
        out = os.path.join(path_data, '03_StreetNetworkProperties')
        np.savetxt(os.path.join(out, 'correlation_v_big.csv'), correlation_matrix, fmt='%.2f')

    # zero mean, variance 1 of all features
    scaler = StandardScaler()
    x = scaler.fit_transform(x)

    # principal component analysis
    pca = PCA()
    pca.fit(x)
    x_pca = pca.transform(x)  # = principal components!

    # data transformation to dataframe
    pca_data = pd.DataFrame(x_pca)
    cls = []
    for i in range(pca_data.shape[1]):
        cls.append('PC' + str(i + 1))
    pca_data.columns = cls
    pca_data = pd.concat((pca_data, prop.success_perc), axis=1)

    # regression model, no PC selection
    f = ''
    for c in cls:
        f += c
        f += ' + '
    model = smf.ols(formula='success_perc ~ ' + f[:-2], data=pca_data)
    results = model.fit()
    print(results.summary())

    # Holm-Bonferroni correction
    print('\nSignificant PCs after Holm-Bonferroni adjustment:')
    m = 31
    sign_pc = []
    for i in range(m):
        rank = i+1
        alpha_adj = 0.05 / (m + 1 - rank)
        if results.pvalues.sort_values()[i] < alpha_adj:
            print(results.pvalues.sort_values().keys()[i])
            sign_pc.append(results.pvalues.sort_values().keys()[i])
        else:
            break

    # pca.components_ are the eigenvectors (norm=1)
    # explained_variance_ are the eigenvalues
    # loadings = Eigenvectors + √Eigenvalues
    eigenv = pca.components_.T
    loadings = eigenv * np.sqrt(pca.explained_variance_)
    varimax_rot_loadings = fa._ortho_rotation(loadings).T

    # strongly loading features of significant PCs (except intercept)
    print('\nPCs with strongly loading features:')
    mx = np.zeros((30, 0))
    for pc in sign_pc[1:]:
        pc = int(pc[2:])
        mx = np.concatenate((mx, varimax_rot_loadings[:, pc - 1:pc]), axis=1)
        ix = np.where(np.abs(varimax_rot_loadings[:, pc - 1]) > 0.6)[0]
        for i in ix:
            print('PC', pc, cols[i])

    # regression model, PC selection
    f2 = ''
    for c in sign_pc[1:]:
        f2 += c
        f2 += ' + '
    model2 = smf.ols(formula='success_perc ~ ' + f2[:-2], data=pca_data)
    results2 = model2.fit()
    print('\nAdjusted R² (all PC):    {:.3f}'.format(results.rsquared_adj))
    print('Adjusted R² (selection): {:.3f}'.format(results2.rsquared_adj))

    # pearson correlation coefficients with success percentage
    print('\nPearson correlation of selected features with success percentage:')
    features = ['detour_to_mean_segment_ratio', 'detour_to_mean_deadend_ratio', 'graph_density']
    for ft in features:
        print(ft, ' {:.3f}'.format(stats.pearsonr(prop[ft], prop.success_perc)[0]))


if __name__ == '__main__':
    '''
    - script to compute regression models
    
    -> select city or cities
    -> select area extent
    '''

    #####################################################
    path_data = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), '01_Data')

    # ARGUMENTS TO SET
    # ------------------------------------------------------------------------------------#
    cities = ['01_Vienna']  # 01_Vienna or 02_Mexico or 03_Djibouti or all 3
    size = 'big'  # big, medium, small
    # ------------------------------------------------------------------------------------#

    properties = pd.DataFrame()
    path_out = os.path.join(path_data, '03_StreetNetworkProperties')

    for city in cities:
        path_orig = os.path.join(path_data, '01_Original', city)
        path_properties = os.path.join(path_data, '03_StreetNetworkProperties', size)
        files = [f for f in os.listdir(path_properties) if city[3:].lower() in f]
        datasets = ['vienna_3000_agents_and_100_routes_our_approach_vienna_best_perc.csv',
                    'mexico_3000_agents_and_100_routes_our_approach_vienna_best_perc.csv',
                    'djibouti_3000_agents_and_100_routes_our_approach_mexico_best_perc.csv']

        # street network properties
        properties_c = pd.DataFrame()
        for file in files:
            result = pd.read_csv(os.path.join(path_properties, file))
            result.insert(0, 'city', city)
            properties_c = pd.concat((properties_c, result), ignore_index=True)

        # success percentage of simulations
        dataset_ix = 0 if city == '01_Vienna' else 1 if city == '02_Mexico' else 2 if city == '03_Djibouti' else 999
        data = AgentData(os.path.join(path_orig, datasets[dataset_ix]))
        success = data.success_per_route().percentage

        properties = pd.concat((properties, pd.concat((properties_c, success.rename('success_perc')), axis=1)))

    # clean data (drop NaN)
    properties = properties.dropna().reset_index(drop=True)

    # principal component regression
    principal_component_regression(properties)
