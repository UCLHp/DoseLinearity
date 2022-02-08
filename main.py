import datetime
import numpy as np
import pandas as pd
import PySimpleGUI as sg


# Pull inital data from DB
# operator list
Op = ['AGr', 'AW', 'TNC', 'CG']
# gantry list
G = ['Gantry 1', 'Gantry 2', 'Gantry 3', 'Gantry 4']
# chamber list
Roos = ['3126','3128','3131','3132']
Semiflex = ['142438','142586','142587']
# electrometer list
El = ['92579','92580','92581']
# voltage list
V = [-400,-200,0,200,400]

# electrometer range list
Rng = ['Low','Medium','High']
# chamber type list
Chtype = ['Roos', 'Semiflex']
Ch = []


### Helper functions
# results analysis
def r_analysis(rlist, mulist):
    R = []
    for lst in rlist:
        R.append([x for x in lst if x != '']) # remove blank readings
    
    # preallocate some vars
    vals = []
    means = []
    stdevs = []
    mu = []
    text_means = [] # useful for gui
    index = [] # useful for gui
    # loop through data and process
    idx=-1
    for r, m in zip(R, mulist):
        idx += 1
        if r:
            index.append(str(idx))
            r = [float(i) for i in r]
            vals.append(r)
            means.append(np.mean(r))
            stdevs.append(np.std(r))
            #text_means.append("%.3f" % np.mean(r))
            mu.append(float(m))

    # catch a naughty mistake
    if len(mu)<2:
        sg.popup('Insufficient Results', 'Measure more than one dose')

    # perform analysis
    r_ratios = []
    mu_ratios = []
    ratio_diffs = []
    for i in range(len(mu)):
        r_ratios.append(means[i]/means[0])
        mu_ratios.append(mu[i]/mu[0])
        ratio_diffs.append(r_ratios[i]/mu_ratios[i]*100-100)
    # convert results to dict
    readings = {}
    readings['MU']=mu
    readings['Rmean']=means
    readings['Rdifflinearity']=ratio_diffs
    readings['Rstd']=stdevs
    readings['Rratio']=r_ratios
    readings['MUratio']=mu_ratios
    readings['R']=vals
    readings['MUindex']=index
    return readings

# csv export
def to_df(keys=None, new_keys=None, values=None):
    dict_csv = { k: values[k] for k in keys }
    if new_keys:
        for new_key, old_key in zip(new_keys,keys):
            dict_csv[new_key] = dict_csv.pop(old_key)
    
    if isinstance(list(dict_csv.values())[0],list):
        df_csv = pd.DataFrame(dict_csv)
    else:
        df_csv = pd.DataFrame.from_records([dict_csv])
    print(df_csv)
    return df_csv

# GUI
#theme
sg.theme('Dark2')

#equipment
plt_layout = [
    [sg.Image('pickles_small.png')],
    #[sg.Canvas(key='-Canvas-')]
]
sess0_layout = [
    [sg.T('Dose Linearity Session Results:', font=['bold',15])],
    [sg.T('')],
    [sg.T('Session Date', justification='right', size=(12,1)), sg.Input(key='ADate', size=(17,1)),
        sg.CalendarButton('yyyy-mm-dd hh:mm:ss', target='ADate',close_when_date_chosen=True, no_titlebar=False, key='-CalB-')],
    [sg.T('Operator 1', justification='right', size=(12,1)), sg.DD(Op, size=(12,1), key='-Op1-')],
    [sg.T('Operator 2', justification='right', size=(12,1)), sg.DD(Op, size=(12,1), key='-Op2-')],
    [sg.T('Gantry', justification='right', size=(12,1)), sg.DD(G, size=(12,1), enable_events=True, key='-G-')], 
    [sg.T('')],  
]
sess1_layout = [
    [sg.T('Temperature', justification='right', size=(12,1)), sg.Input(key='Temp', enable_events=True, size=(12,1))],
    [sg.T('Pressure', justification='right', size=(12,1)), sg.Input(key='Press', enable_events=True, size=(12,1))],
    [sg.T('')],
]
sess2_layout = [
    [sg.T('Chamber Type', justification='right', size=(12,1)), sg.DD(Chtype, size=(12,1), enable_events=True, key='-Chtype-')],
    [sg.T('Chamber', justification='right', size=(12,1)), sg.Combo(Ch, size=(12,1), enable_events=True, key='-Ch-')],
    [sg.T('')],
]
sess3_layout = [
    [sg.T('Electrometer', justification='right', size=(12,1)), sg.DD(El, size=(12,1), enable_events=True, key='-El-')],
    [sg.T('Voltage (V)', justification='right', size=(12,1)), sg.DD(V, size=(12,1), enable_events=True, key='-V-')],
    [sg.T('')],
]

#results
mu_layout = [ 
    [sg.T('MU Spot Weight:')],
    [sg.T('MU0', size=(3,1)), sg.InputText(key='mu0', disabled=True, default_text=5, size=(7,1), enable_events=True)],
    [sg.T('MU1', size=(3,1)), sg.InputText(key='mu1', disabled=True, default_text=10, size=(7,1), enable_events=True)],
    [sg.T('MU2', size=(3,1)), sg.InputText(key='mu2', disabled=True, default_text=20, size=(7,1), enable_events=True)],
    [sg.T('MU3', size=(3,1)), sg.InputText(key='mu3', disabled=True, default_text=30, size=(7,1), enable_events=True)],
    [sg.T('MU4', size=(3,1)), sg.InputText(key='mu4', disabled=True, default_text=40, size=(7,1), enable_events=True)],
    [sg.T('MU5', size=(3,1)), sg.InputText(key='mu5', disabled=True, default_text=50, size=(7,1), enable_events=True)],
]
e_layout = [
    [sg.T('Electrometer Range:')],
    [sg.DD(Rng, size=(15,1), default_value=Rng[1], enable_events=True, key='-Rng0-')],
    [sg.DD(Rng, size=(15,1), default_value=Rng[1], enable_events=True, key='-Rng1-')],
    [sg.DD(Rng, size=(15,1), default_value=Rng[1], enable_events=True, key='-Rng2-')],
    [sg.DD(Rng, size=(15,1), default_value=Rng[2], enable_events=True, key='-Rng3-')],
    [sg.DD(Rng, size=(15,1), default_value=Rng[2], enable_events=True, key='-Rng4-')],
    [sg.DD(Rng, size=(15,1), default_value=Rng[2], enable_events=True, key='-Rng5-')],
]
r1_layout = [
    [sg.T('R1 (nC):')],
    [sg.InputText(key='r01', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r11', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r21', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r31', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r41', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r51', default_text='', size=(7,1), enable_events=True)],
]
r2_layout = [
    [sg.T('R2 (nC):')],
    [sg.InputText(key='r02', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r12', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r22', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r32', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r42', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r52', default_text='', size=(7,1), enable_events=True)],
]
r3_layout = [
    [sg.T('R3 (nC):')],
    [sg.InputText(key='r03', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r13', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r23', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r33', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r43', default_text='', size=(7,1), enable_events=True)],
    [sg.InputText(key='r53', default_text='', size=(7,1), enable_events=True)],
]
rm_layout = [
    [sg.T('R avg (nC):')],
    [sg.InputText(default_text='', disabled=True, justification='right', key='rm0', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='rm1', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='rm2', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='rm3', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='rm4', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='rm5', size=(10,1))],
]
dr_layout = [
    [sg.T('Linearity Diff (%):')],
    [sg.InputText(default_text='', disabled=True, justification='right', key='dr0', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='dr1', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='dr2', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='dr3', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='dr4', size=(10,1))],
    [sg.InputText(default_text='', disabled=True, justification='right',  key='dr5', size=(10,1))],
]

#buttons
button_layout = [
    [sg.T('')],
    [sg.B('Submit', key='-Submit-'),
     sg.B('Analyse Session', key='-AnalyseS-'),
     sg.B('Analyse Database', key='-AnalyseD-'),
     sg.B('Export to csv', key='-Export-'),
     sg.B('Clear', key='-Clear-'),
     sg.B('Cancel', key='-Cancel-')],
]

#combine layout elements
layout = [
    [sg.Column(sess0_layout), sg.Column(plt_layout)],
    [sg.Column(sess1_layout), sg.Column(sess2_layout), sg.Column(sess3_layout)],
    [sg.Column(mu_layout),sg.Column(e_layout),sg.Column(r1_layout),sg.Column(r2_layout),sg.Column(r3_layout),sg.Column(rm_layout),sg.Column(dr_layout)],
    [button_layout],
]

# Create the GUI Window
window = sg.Window('Dose Linearity', layout)
print(window)

# Event Loop listens out for events e.g. button presses
session_analysed=False
while True:
    event, values = window.read()
    ### reset analysed flags if there is just about any event
    if event not in ['-Submit-','-AnalyseS-','-AnalyseD-','-Export-']:
        session_analysed=False
        
    ### Button events
    if event == '-Submit-': # user clicks Submit
        if session_analysed:
            ### catch invlid entires before submission
            if values['ADate'] == "":
                print("ENTER A VALID DATE")
            if values['-Op2-'] != "" and values['-Op2-']==values['-Op1-']:
                print("OPERATORS MUST BE UNIQUE")        
            print('Submitted to database') ### submit results to access database here
        else:
            sg.popup('Analysis Required', 'Analyse the session before submitting to database')

    if event == '-AnalyseD-':
        print("Analysing Database...") ### run SQL query and graphing analysis here

    if event == '-Export-':
        if session_analysed:
            print("Exporting to csv...") ### save all results to a csv file here
            #session csv
            old_keys = ['ADate', '-Op1-', '-Op2-','-G-','Temp','Press','-Chtype-','-Ch-','-El-','-V-']
            new_keys = ['ADate', 'Operator 1', 'Operator 2', 'Machine', 'Temperature', 'Pressure', 'ChamberType', 'ChamberID','ElectrometerID','Voltage']
            session_df = to_df(keys=old_keys, new_keys=new_keys, values=values)
            results_keys = list(readings.keys())
            results_df = to_df(keys=results_keys, values=readings)
        else:
            sg.popup('Analysis Required', 'Analyse the session before exporting to csv')

    if event == '-Clear-':
        session_analysed=False
        print("Form cleared...") ### clear fields in GUI
        #except the following:
        except_list = ['-CalB-'] # calendar button text
        except_list.extend(['mu'+str(i) for i in range(6)]) # MU spot weights
        except_list.extend(['-Rng'+str(i)+'-' for i in range(6)]) # electrometer range
        for key in values:
            if key not in except_list:
                window[key]('')

    if event == sg.WIN_CLOSED or event == '-Cancel-': # user closes window or clicks cancel
        print("Form closed without saving...")
        break

    if event == '-AnalyseS-':
        session_analysed = True
        ### analyse data in session here
        # process measurements
        r_list = [
            [values['r01'], values['r02'], values['r03']],
            [values['r11'], values['r12'], values['r13']],
            [values['r21'], values['r22'], values['r23']],
            [values['r31'], values['r32'], values['r33']],
            [values['r41'], values['r42'], values['r43']],
            [values['r51'], values['r52'], values['r53']],
        ]
        mu_list = [
            values['mu0'],
            values['mu1'],
            values['mu2'],
            values['mu3'],
            values['mu4'],
            values['mu5'],
        ]
        readings = r_analysis(r_list,mu_list)
        # update GUI
        for i in range(len(readings['MUindex'])):
            rm_idx = 'rm'+readings['MUindex'][i]
            window[rm_idx](readings['Rmean'][i]) # average reading
            dr_idx = 'dr'+readings['MUindex'][i]
            window[dr_idx](readings['Rdifflinearity'][i]) # linearity difference

    ### Field events
    if event == '-Chtype-':   # chamber type dictates chamber list
        print(values['-Chtype-'])
        if values['-Chtype-'] == 'Roos':
            Ch = Roos
        elif values['-Chtype-'] == 'Semiflex':
            Ch = Semiflex
        else:
            Ch = []
        window['-Ch-'].update(values=Ch, value='') # update Ch combo box

window.close()
