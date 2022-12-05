import os
import pandas as pd
import numpy as np


if __name__ == '__main__':
    '''
    - script to analyse the taken node ratios of all taken nodes of Vienna's 6 simulation datasets 
    - computation of the node ratio threshold
    '''

    #####################################################
    path_data = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), '01_Data')

    city = '01_Vienna'

    path_orig = os.path.join(path_data, '01_Original', city)
    path_sub = os.path.join(path_data, '02_Subgraphs', city)
    path_graph = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'nx_graph_with_ec_with_bearing' in f][0])
    path_routes = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'random_routes' in f][0])
    files = [f for f in os.listdir(path_orig) if 'our_approach' in f]

    folder = ['dji_fch', 'dji_prc', 'mex_fch', 'mex_prc', 'vie_fch', 'vie_prc']
    routeIDs = list(range(100))


    # area threshold definition based on simulation results of VIENNA
    # X% of all taken nodes / X% of all SUCCESSFULLY taken nodes, below chosen percentage (OPTION 1+2)
    # X% of all taken routes / X% of all SUCCESSFULLY taken routes, below chosen percentage (OPTION 3+4)
    percentages = [0.99, 0.999, 0.9999]
    above_all, above_suc, routes_all = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    count_all, count_suc = [], []

    # loop routes
    for r in routeIDs:
        print(r)
        all_rx = pd.DataFrame(columns=['id', 'x', 'y', 'l'])
        vals_max_all = pd.DataFrame()
        vals_max_suc = pd.DataFrame()
        # loop folders
        for f in folder:
            path = os.path.join(path_sub, 'boundingbox', 'alltakennodes', f, 'route_{:02d}_taken.csv'.format(r))
            tk = pd.read_csv(path)
            tk = tk.iloc[:, 1:]
            tk['l'] = round(tk['l'], 6)
            tk['dataset'] = f
            vals_max_all[f] = [tk.l.max()]
            vals_max_suc[f] = [tk[tk.success == 1.0].l.max()]
            all_rx = pd.concat([all_rx, tk], ignore_index=True)
        temp = all_rx.groupby(['agent_id', 'dataset', 'success'], axis=0, as_index=False).l.max()
        routes_all = pd.concat([routes_all, temp], ignore_index=True)
        above_all = pd.concat([above_all, all_rx[all_rx.l > 1.05]], ignore_index=True)
        count_all.append(len(all_rx))
        above_suc = pd.concat([above_suc, all_rx[(all_rx.l > 1.05) & (all_rx.success == 1)]], ignore_index=True)
        count_suc.append(len(all_rx[all_rx.success == 1]))

    ####################################################################################################

    thresh_all_nodes, thresh_suc_nodes = [], []
    thresh_all_routes, thresh_suc_routes = [], []

    # threshold for all taken nodes (OPTION 1)
    total_all = sum(count_all)
    sorted_above_all = above_all.sort_values(by='l')
    for p in percentages:
        ix_all = int(total_all - total_all * p)
        thresh_all_nodes.append(sorted_above_all.iloc[-ix_all].l)

    # threshold for all SUCCESSFULLY taken nodes (OPTION 2)
    total_suc = sum(count_suc)
    sorted_above_suc = above_suc.sort_values(by='l')
    for p in percentages:
        ix_suc = int(total_suc - total_suc * p)
        thresh_suc_nodes.append(sorted_above_suc.iloc[-ix_suc].l)

    # threshold for all taken routes / all SUCCESSFULLY taken routes (OPTION 3+4)
    for p in percentages:
        thresh_all_routes.append(np.quantile(routes_all.l, p))
        thresh_suc_routes.append(np.quantile(routes_all[routes_all.success == 1].l, p))

    # area threshold ratios for four different options
    area_threshs = pd.DataFrame()
    area_threshs['option1'] = thresh_all_nodes
    area_threshs['option2'] = thresh_suc_nodes
    area_threshs['option3'] = thresh_all_routes
    area_threshs['option4'] = thresh_suc_routes
    area_threshs = area_threshs.transpose()
    area_threshs.columns = ['{:.2f}%'.format(percentages[0]*100),
                            '{:.2f}%'.format(percentages[1]*100),
                            '{:.2f}%'.format(percentages[2]*100)]

    save_path = os.path.join(path_data, '02_Subgraphs', 'threshold_ratios.csv')
    area_threshs.to_csv(save_path, float_format='%.3f')
