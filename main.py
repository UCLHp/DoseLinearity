import datetime
import time
import os
from turtle import color
import pandas as pd
import numpy as np
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database_df as db
import field_check as fc

### Action levels
CoV_threshold = 0.5
Chi_threshold = [0,0.2]#[99.9,100.1]

### Session and Results Classes
class DLsession:
    def __init__(self):
        self.ADate = None
        self.Op1 = None
        self.Op2 = None
        self.G = None
        self.GA = None
        self.E = None
        self.Eid = None
        self.V = None 
        self.Ctype =None
        self.Cid = None 
        self.T = None
        self.P =None
        self.LinearityPass = 'NA'
        self.VarPass = 'NA'
        self.Comment = None
        self.fname = 'session.csv' 

    def analysis(self,values):
        self.ADate = values['ADate']
        self.Op1 = values['-Op1-']
        self.Op2 = values['-Op2-']
        self.G = values['-G-']
        self.GA = values['GA']
        self.E = values['EN']
        self.Eid = values['-El-']
        self.V = values['-V-'] 
        self.Ctype = values['-Chtype-']
        self.Cid = values['-Ch-']  
        self.T = values['Temp']
        self.P = values['Press']
        self.Comment = values['-ML-']


class DLresults():
    def __init__(self):
        self.RTimestamp = []
        self.ADate = []
        self.MUindex = []
        self.MU = []
        self.Rmean = []
        self.Rdifflinearity = []
        self.Rstd = []
        self.Rratio = []
        self.MUratio = []
        self.R = []
        self.cov = []
        self.VarPass = []
        self.analysed = False
        self.fname = 'results.csv'

    def analysis(self,rlist,mulist):
        R_filt = []
        for lst in rlist:
            R_filt.append([x for x in lst if x != '']) # remove blank readings
        
        # loop through data and process
        idx=-1
        for r, m in zip(R_filt, mulist):
            idx += 1
            if r:
                r = [float(i) for i in r]                    
                self.MUindex.append(str(idx+1))
                self.R.append(r)
                self.Rmean.append(np.mean(r))
                self.Rstd.append(np.std(r))
                self.MU.append(float(m))

        # catch a naughty mistake
        if len(self.MU)<2:
            sg.popup('Insufficient Results', 'Measure more than one dose')
            self.analysed = False
        else:
            self.analysed=True

        # perform analysis
        for i in range(len(self.MU)):
            self.RTimestamp.append(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-4])
            self.Rratio.append(self.Rmean[i]/self.Rmean[0])
            self.MUratio.append(self.MU[i]/self.MU[0])
            self.Rdifflinearity.append(self.Rratio[i]/self.MUratio[i]*100-100)
            self.cov.append(self.Rstd[i]/self.Rmean[i]*100)
            time.sleep(0.075)   
    
    # linear fit
    def _fit(self):
        mu = [0]
        mu.extend(self.MU)
        r = [0]
        r.extend(self.Rmean)
        w = [1]*len(r)
        w[0] = 1e6
        a,b = np.polyfit(mu,r,1,w=w)
        return a, b

    # coefficient of determination
    def _cod(self,x,y,a,b):
        ymean = np.mean(y)
        y_fit = a*x+b
        ssres = np.sum((y-y_fit)**2)
        sstot = np.sum((y-ymean)**2)
        cod = (1 - ssres/sstot)*100
        return cod

    # Pearson's Chi Square test
    def _prn(self,x,y,a,b):
        '''prn = ChiSq[predicted from MU ratios] - ChiSq[linear fit]'''
        chi=[]
        y_pred = x/x[0]*y[0]
        y_fit = a*x+b
        prn = np.sum(y**2/y_pred) - np.sum(y**2/y_fit)
        return abs(prn)
    
    # perform linear fit after analysis
    def fit_data(self):
        x = np.array(self.MU)
        y = np.array(self.Rmean)
        Rmin = np.array([np.array(i).min() for i in self.R])
        Rmax = np.array([np.array(i).max() for i in self.R])
        yerr = np.empty((2, y.shape[0]))
        yerr[0,:] = y-Rmin
        yerr[1,:] = Rmax-y
        a, _ = self._fit()
        x_ref = np.array(range(int(x[-1]+1)))
        y_ref = a*np.array(x_ref)
        #cod = self._cod(x,y,a,0)
        prn = self._prn(x,y,a,0)
        return x,y,yerr,x_ref,y_ref,prn
    
    # timestamp all measurements
    def assign_session(self,adate):
        for t in self.RTimestamp:
            self.ADate.append(adate)


# Pull inital data from DB
try:
    G, Chtype, V, Rng, Op, Roos, Semiflex, Ch, El, baseline_readings =\
        db.populate_fields()
except:
    print("Conection failed...")
    sg.popup_error("Export all measurements to .csv!",
    title="Cannot Connect to Database!",
    image = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db_error.png')),
    background_color="black",
    keep_on_top=True)
x_ref = baseline_readings[0]
y_ref = baseline_readings[1]

### Helper functions
# csv export
def export_csv(data=None, keys=None, new_keys=None, dname=None):
    # create dictionary from class data
    dict = vars(data)

    # create timestamped folder
    csv_time = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_dir = dname+os.sep+csv_time
    os.makedirs(csv_dir, exist_ok=True)

    # retain specified keys and rename if desired
    dict = { k: dict[k] for k in keys }
    if new_keys:
        for new_key, old_key in zip(new_keys,keys):
            dict[new_key] = dict.pop(old_key)  

    # write to csv
    df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
    fname = csv_dir+os.sep+data.fname
    df.to_csv(fname, index=False)
    print("Saved: "+fname)

# dataframe conversion
def convert2df(data=None, keys=None, new_keys=None):
    # create dictionary from class data
    dict = vars(data)

    # retain specified keys and rename if desired
    dict = { k: dict[k] for k in keys }
    if new_keys:
        for new_key, old_key in zip(new_keys,keys):
            dict[new_key] = dict.pop(old_key)  

    # write to dataframe
    df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
    return df

# graph plotting
_VARS = {'fig_agg': False, 'pltFig': False}

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def format_fig(xData,yData):
    plt.plot(xData,yData,'--k',linewidth=1)
    plt.title('Results', fontsize=10, fontweight='bold',color='w')
    plt.xlabel('Mean Reading (nC)', fontsize=8, fontweight='bold',color='w')
    plt.ylabel('Spot MU', fontsize=8, fontweight='bold',color='w')
    plt.xlim([xData[0], xData[-1]+1])
    plt.ylim([yData[0], yData[-1]+1])
    plt.xticks(fontsize=8)
    plt.yticks(np.arange(yData[0],yData[-1]+1,1), fontsize=8)
    plt.tick_params(colors='w')
    plt.grid(visible=True)
    plt.tight_layout()

def init_figure(xref,yref):
    _VARS['pltFig'] = plt.figure(figsize=(4.75,3), facecolor='#404040')
    format_fig(xref,yref)
    _VARS['fig_agg'] = draw_figure(window['figCanvas'].TKCanvas, _VARS['pltFig'])

def update_fig(x,y,yerr,xref,yref):
    _VARS['fig_agg'].get_tk_widget().forget()
    plt.clf()
    format_fig(xref, yref)
    if x is not None:
        plt.errorbar(x, y, yerr=yerr, fmt='g.', ecolor='k', elinewidth=1)
        plt.xlim([xref.min(),xref.max()+1])
        plt.ylim([yref.min(),y.max()+yerr.max()+1])
        plt.yticks(np.arange(yref.min(),yref.max()+1,1), fontsize=8)
    _VARS['fig_agg'] = draw_figure(
        window['figCanvas'].TKCanvas, _VARS['pltFig'])

### GUI window function
def build_window():
    #theme
    sg.theme('Dark2')

    #equipment
    img_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pickles_small.png'))
    plt_layout = [[sg.Image(img_file)]]
    plt_layout = [[sg.Canvas(key='figCanvas')]]

    sess0_layout = [
        [sg.T('Dose Linearity:', font=['bold',18])],
        [sg.T('')],
        [sg.T('Date', justification='right', size=(10,1)), sg.Input(key='ADate', size=(18,1))],
        [sg.T('', size=(10,1)), sg.CalendarButton('dd/mm/yyyy hh:mm:ss', font=('size',9), target='ADate',format='%d/%m/%Y %H:%M:%S', close_when_date_chosen=True, no_titlebar=False, key='-CalB-')],
        [sg.T('Operator 1', justification='right', size=(10,1)), sg.DD(Op, size=(10,1), key='-Op1-')],
        [sg.T('Operator 2', justification='right', size=(10,1)), sg.DD(Op, size=(10,1), key='-Op2-')],
        [sg.T('Temp', justification='right', size=(10,1)), sg.Input(key='Temp', enable_events=True, size=(10,1))],
        [sg.T('Pressure', justification='right', size=(10,1)), sg.Input(key='Press', enable_events=True, size=(10,1))],
    ]
    sess1_layout = [
        [sg.T('Gantry', justification='right', size=(12,1)), sg.DD(G, size=(11,1), enable_events=True, key='-G-')],
        [sg.T('Gantry Angle', justification='right', size=(12,1)), sg.Input(key='GA', enable_events=True, default_text='0', size=(11,1))],
        [sg.T('Energy', justification='right', size=(12,1)), sg.Input(key='EN', enable_events=True, default_text='160', size=(11,1))],
    ]
    sess2_layout = [
        [sg.T('Chamber Type', justification='right', size=(12,1)), sg.DD(Chtype, size=(11,1), enable_events=True, key='-Chtype-')],
        [sg.T('Chamber', justification='right', size=(12,1)), sg.Combo(Ch, size=(11,1), enable_events=True, key='-Ch-')],
    ]
    sess3_layout = [
        [sg.T('Electrometer', justification='right', size=(12,1)), sg.DD(El, size=(11,1), enable_events=True, key='-El-')],
        [sg.T('Voltage (V)', justification='right', size=(12,1)), sg.DD(V, size=(11,1), enable_events=True, key='-V-')],
    ]

    #results
    mu_layout = [ 
        [sg.T('MU per Spot:')],
        [sg.T('MU1', size=(3,1)), sg.InputText(key='mu1', disabled=True, default_text=5, size=(7,1), enable_events=True)],
        [sg.T('MU2', size=(3,1)), sg.InputText(key='mu2', disabled=True, default_text=10, size=(7,1), enable_events=True)],
        [sg.T('MU3', size=(3,1)), sg.InputText(key='mu3', disabled=True, default_text=14, size=(7,1), enable_events=True)],
        [sg.T('MU4', size=(3,1)), sg.InputText(key='mu4', disabled=True, default_text=20, size=(7,1), enable_events=True)],
        [sg.T('MU5', size=(3,1)), sg.InputText(key='mu5', disabled=True, default_text=25, size=(7,1), enable_events=True)],
    ]
    e_layout = [
        [sg.T('Electrometer Range:')],
        [sg.DD(Rng, size=(15,1), default_value=Rng[1], enable_events=True, key='-Rng1-')],
        [sg.DD(Rng, size=(15,1), default_value=Rng[1], enable_events=True, key='-Rng2-')],
        [sg.DD(Rng, size=(15,1), default_value=Rng[1], enable_events=True, key='-Rng3-')],
        [sg.DD(Rng, size=(15,1), default_value=Rng[2], enable_events=True, key='-Rng4-')],
        [sg.DD(Rng, size=(15,1), default_value=Rng[2], enable_events=True, key='-Rng5-')],
    ]
    r1_layout = [
        [sg.T('R1 (nC):')],
        [sg.InputText(key='r11', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r21', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r31', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r41', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r51', default_text='', size=(7,1), enable_events=True)],
    ]
    r2_layout = [
        [sg.T('R2 (nC):')],
        [sg.InputText(key='r12', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r22', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r32', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r42', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r52', default_text='', size=(7,1), enable_events=True)],
    ]
    r3_layout = [
        [sg.T('R3 (nC):')],
        [sg.InputText(key='r13', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r23', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r33', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r43', default_text='', size=(7,1), enable_events=True)],
        [sg.InputText(key='r53', default_text='', size=(7,1), enable_events=True)],
    ]
    rm_layout = [
        [sg.T('R avg (nC):')],
        [sg.T('', background_color='lightgray', text_color='black', justification='right',  key='rm1', size=(10,1))],
        [sg.T('', background_color='lightgray', text_color='black', justification='right',  key='rm2', size=(10,1))],
        [sg.T('', background_color='lightgray', text_color='black', justification='right',  key='rm3', size=(10,1))],
        [sg.T('', background_color='lightgray', text_color='black', justification='right',  key='rm4', size=(10,1))],
        [sg.T('', background_color='lightgray', text_color='black', justification='right',  key='rm5', size=(10,1))],
    ]
    dr_layout = [
        [sg.T('Coeff of Var (%):')],
        [sg.T('', background_color='lightgray', justification='right', key='dr1', size=(10,1))],
        [sg.T('', background_color='lightgray', justification='right', key='dr2', size=(10,1))],
        [sg.T('', background_color='lightgray', justification='right', key='dr3', size=(10,1))],
        [sg.T('', background_color='lightgray', justification='right', key='dr4', size=(10,1))],
        [sg.T('', background_color='lightgray', justification='right', key='dr5', size=(10,1))],
    ]
    chi_layout = [
        [sg.T('Chi Sqaure')],[sg.T('', background_color='lightgray', justification='right', key='Chi', size=(10,1))]
    ]
    ml_layout = [
        [sg.Multiline('', key='-ML-', enable_events=True, size=(96,5))],
    ]

    #buttons
    button_layout = [
        [sg.B('Submit to Database', disabled=True, key='-Submit-'),
        sg.B('Analyse Session', key='-AnalyseS-'),
        sg.FolderBrowse('Export to CSV', key='-CSV_WRITE-', disabled=True, target='-Export-'), sg.In(key='-Export-', enable_events=True, visible=False),
        sg.B('Clear', key='-Clear-'),
        sg.B('End Session', key='-Cancel-')],
    ]

    #combine layout elements
    layout = [
        [sg.Column(sess0_layout), sg.Column(plt_layout)],
        [sg.Frame('Equipment',[[sg.Column(sess1_layout), sg.Column(sess2_layout), sg.Column(sess3_layout)]])],
        [sg.Frame('Measurements',[[sg.Column(mu_layout),sg.Column(e_layout),sg.Column(r1_layout),sg.Column(r2_layout),sg.Column(r3_layout),
         sg.Column(rm_layout),sg.Column(dr_layout),sg.Column(chi_layout)]])],
        [sg.Frame('Comments', ml_layout)],
        [button_layout],
    ]

    icon_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon', 'cucumber2_yd4_icon.ico'))
    return sg.Window('Dose Linearity', layout, finalize=True, icon=icon_file)


### Initialise data objects
results = DLresults()
session = DLsession()
session_keys = [i for i in vars(session).keys() if i not in 'fname']
new_keys = ['ADate', 'Operator 1', 'Operator 2', 'MachineName', 'GA', 'Energy',
'Electrometer', 'Voltage', 'ChamberType', 'Chamber', 'Temperature', 'Pressure', 'LinearityPass', 'RepeatabilityPass', 'Comments']
results_keys = [i for i in vars(results).keys() if i not in ['analysed', 'fname', 'cov']]

field_check = fc.field_check(Op, G, Roos+Semiflex, El, [str(i) for i in V])

### Generate GUI
window = build_window()
session_analysed = False
init_figure(x_ref,y_ref)

# Event Loop listens out for events e.g. button presses
while True:
    event, values = window.read()
    ### reset analysed flag if there is just about any event
    if event not in ['-Submit-','-AnalyseS-','-Export-','-ML-',sg.WIN_CLOSED]:
        session_analysed=False
        window['-CSV_WRITE-'](disabled=True) # disable csv export button
        window['-Submit-'](disabled=True) # disable access export button
        
    ### Button events
    if event == '-Submit-': ### Submit data to database
        if session_analysed:
            checked, msg = field_check.check(values)
            if checked:
                df_session = convert2df(session, session_keys, new_keys)
                df_results = convert2df(results, results_keys)
                db.write_to_db(df_session,df_results)
                print('Data submitted to database.')
                session_analysed=True
                window['-Submit-'](disabled=True) # disable access export button
                window['-AnalyseS-'](disabled=True) # disable access export button
                window['ADate'](disabled=True) # freeze session ID
            else:
                session_analysed = False
                window['-Submit-'](disabled=False) # disable access export button
                print(msg)
        else:
            sg.popup('Analysis Required', 'Analyse the session before submitting to database')

    if event == '-AnalyseS-': ### Analyse results
        # collect results
        r_list = [
            [values['r11'], values['r12'], values['r13']],
            [values['r21'], values['r22'], values['r23']],
            [values['r31'], values['r32'], values['r33']],
            [values['r41'], values['r42'], values['r43']],
            [values['r51'], values['r52'], values['r53']],
        ]
        mu_list = [
            values['mu1'],
            values['mu2'],
            values['mu3'],
            values['mu4'],
            values['mu5'],
        ]
        # analyse valid results
        try:
            # convert string to float
            for k in r_list:
                for n in range(3):
                    if k[n] != '':
                        k[n] = float(k[n])
            mu_list = [float(i) if i != '' else i for i in mu_list]
            # analyse results
            results.__init__()
            results.analysis(r_list,mu_list)
            results.assign_session(values['ADate'])
            session_analysed = results.analysed
            # record session info
            session.analysis(values)
        except:
            sg.popup("Invalid Values", "Enter valid readings")
            # record session info
            session_analysed = False
            
        # update GUI
        if session_analysed:
            window['-CSV_WRITE-'](disabled=False) # enable Export button
            window['-Submit-'](disabled=False) # enable Export button
            window['ADate'](disabled=True) # freeze session ID
            x,y,yerr,xref,yref,prn = results.fit_data()
            update_fig(x,y,yerr,xref,yref) # plot results
            window['Chi']('%.3f' % prn)
            if Chi_threshold[0] <= prn <= Chi_threshold[1]:
                window['Chi'](background_color='green')
                session.LinearityPass = 'PASS'
            else:
                window['Chi'](background_color='red')  
                session.LinearityPass = 'FAIL'      
        session.VarPass = 'PASS'
        n=0
        for i in range(1,len(mu_list)+1):
            if n<len(results.MUindex) and str(i) == results.MUindex[n]:
                rm_idx = 'rm'+ results.MUindex[n]
                window[rm_idx]('%.3f' % results.Rmean[n]) # format mean to 3dp
                dr_idx = 'dr'+results.MUindex[n]
                cov = results.cov[n]
                window[dr_idx]('%.3f' % cov) # format diff to 3dp
                if abs(cov)>CoV_threshold:
                    window[dr_idx](background_color='red')
                    session.VarPass = 'FAIL'
                    results.VarPass.append('FAIL')
                else:
                    window[dr_idx](background_color='green')
                    results.VarPass.append('PASS')
                n+=1
            else:
                rm_idx = 'rm'+str(i)
                dr_idx = 'dr'+str(i)
                window[rm_idx]('', background_color='lightgray')
                window[dr_idx]('', background_color='lightgray')
        # for i in range(len(results.MUindex)):
        #     rm_idx = 'rm'+ results.MUindex[i]
        #     window[rm_idx]('%.3f' % results.Rmean[i]) # format mean to 3dp
        #     dr_idx = 'dr'+results.MUindex[i]
        #     cov = results.cov[i]
        #     window[dr_idx]('%.3f' % cov) # format diff to 3dp
        #     if abs(cov)>CoV_threshold:
        #         window[dr_idx](background_color='red')
        #     else:
        #         window[dr_idx](background_color='green')


    if event == '-Export-': ### Export results to csv
        if session_analysed and values['-Export-'] != '':
            #session csv
            export_csv(data=session, keys=session_keys, new_keys=new_keys, dname=values['-Export-'])
            #results csv
            export_csv(data=results, keys=results_keys, dname=values['-Export-'])
        elif values['-Export-'] == '':
            sg.popup('Directory Not Selected', 'Choose a valid directory')
        else:
            sg.popup('Analysis Required', 'Analyse the session before exporting to csv')
            
    if event == '-Clear-': ### Clear GUI fields and results
        session_analysed=False
        results.__init__()
        session.__init__()
        print("Session cleared.")
        #except the following:
        except_list = ['-CalB-', '-CSV_WRITE-','figCanvas'] # calendar button text
        except_list.extend(['mu'+str(i) for i in range(6)]) # MU spot weights
        except_list.extend(['-Rng'+str(i)+'-' for i in range(6)]) # electrometer range
        for key in values:
            if key not in except_list:
                window[key]('')
        for i in range(1,6):
            window['dr'+str(i)]('', background_color='lightgray')
            window['rm'+str(i)]('', background_color='lightgray')
        window['Chi']('', background_color='lightgray')
        window['ADate'](disabled=False) # freeze session ID
        window['-AnalyseS-'](disabled=False) # freeze session ID
        update_fig(None,None,None,x_ref,y_ref)

    if event == sg.WIN_CLOSED or event == '-Cancel-': ### user closes window or clicks cancel
        print("Session Ended.")
        break

    ### Populate Chamber ID list
    if event == '-Chtype-':   # chamber type dictates chamber list
        if values['-Chtype-'] == 'Roos':
            Ch = Roos
        elif values['-Chtype-'] == 'Semiflex':
            Ch = Semiflex
        else:
            Ch = []
        window['-Ch-'].update(values=Ch, value='') # update Ch combo box

window.close()
