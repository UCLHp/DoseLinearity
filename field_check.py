import datetime
import PySimpleGUI as sg

# check all fields are compliant
class field_check():
    def __init__(self,Op, G, Ch, El, V):
        self.check_fail = None
        self.Fields = {
            'ADate': 'Date',
            '-Op1-': 'Operator 1',
            '-Op2-': 'Operator 2',
            'Temp': 'Temperature',
            'Press': 'Pressure',
            '-G-': 'Gantry Name',
            'GA': 'Gantry Angle',
            'EN': 'Energy',
            '-Chtype-': 'Chamber Type',
            '-Ch-': 'Chamber ID',
            '-El-': 'Electrometer ID',
            '-V-': 'Voltage'}
        self.Op = Op
        self.G = G
        self.Ch = Ch
        self.El = El
        self.V = V
        self.check_complete = None

    def check(self,values):
        '''
            Parse each GUI field to check the values are valid
        '''        
        
        # helper functions
        def _range_check(value, key, minval, maxval):
            if not maxval >= value >= minval:
                sg.popup("Invalid Value", "Enter a valid value for: "+key)
                return True
            else:
                return False
        
        def _list_check(value, key, combo_list):
            if value not in combo_list:
                sg.popup("Invalid Value", "Enter a value from the dropdown list: "+key)
                return True
            else:
                return False
        
        def _num_check(value, key):
            if value != '': 
                try:
                    float(value) < 0
                    return False
                except:
                    sg.popup("Value must be blank or >= 0: "+key)
                    return True
            else:
                return False

        # catch blank fields
        for key in self.Fields.keys():
            if values[key] == "" and key != "-Op2-":
                self.check_fail = True
                sg.popup("Empty Field","Enter a value for: "+self.Fields[key])
                return False,1

        # parse date field
        try:
            adate = datetime.datetime.strptime(values['ADate'],"%d/%m/%Y %H:%M:%S")
        except:
            self.check_fail = True
            sg.popup("Invalid Value", "Enter a valid value for: "+self.Fields['ADate'])
            return False,2
        
        # check date is within valid range
        self.check_fail = _range_check(adate,
            self.Fields['ADate'],
             datetime.datetime.strptime("01/01/2022 00:00:00","%d/%m/%Y %H:%M:%S"),
             datetime.datetime.strptime("01/01/2122 00:00:00","%d/%m/%Y %H:%M:%S"),
             )
        if self.check_fail:
            return False,3

        # check combo box fields are valid
        op1 = _list_check(values['-Op1-'],self.Fields['-Op1-'],self.Op) #operator 1
        g = _list_check(values['-G-'],self.Fields['-G-'],self.G) #machine name
        ch = _list_check(values['-Ch-'],self.Fields['-Ch-'],self.Ch) #chamber ID
        el = _list_check(values['-El-'],self.Fields['-El-'],self.El) #electrometer ID
        v = _list_check(str(values['-V-']),self.Fields['-V-'],self.V) #electrometer voltage
        if any([op1,g,ch,el,v]):
            self.check_fail = True
            return False,4

        # check temperature
        try:
           t = _range_check(float(values['Temp']), self.Fields['Temp'], 18., 26.)
        except:
            self.check_fail = True
            return False,5
        if t:
            self.check_fail = True
            return False,6

        # check pressure
        try:
           p = _range_check(float(values['Press']), self.Fields['Press'], 955, 1055)
        except:
            self.check_fail = True
            return False,7
        if p:
            self.check_fail = True
            return False,8

        # check beam energy
        try:
            en = _range_check(float(values['EN']), self.Fields['EN'], 70, 245)
        except:
            self.check_fail = True
            return False,9
        if en:
            self.check_fail = True
            return False,10

        # check gantry angle
        try:
            ga = _range_check(float(values['GA']), self.Fields['GA'], 0, 360)
        except:
            self.check_fail = True
            return False,9.1
        if ga:
            self.check_fail = True
            return False,10.1

        # check readings and MU weightings
        for i in range(5):
            self.check_fail = _num_check(values['mu'+str(i)], 'Spot Weight, MU'+str(i))
            if self.check_fail:
                return False,11
            for k in range(3):
                self.check_fail = _num_check(values['r'+str(i)+str(k+1)], 'R'+str(k+1)+', MU'+str(i))
                if self.check_fail:
                    return False,12

        self.check_complete = True
        return self.check_complete,666
