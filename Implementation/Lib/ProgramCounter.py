import py4hw



class ProgCounter(py4hw.Logic):

    def __init__(self,parent,name,Load_data,Load_Enable,OUT):
        super().__init__(parent, name)

        self.Load_data = self.addIn('Load_data',Load_data)
        self.Load_Enable = self.addIn('Load_Enable',Load_Enable)
        self.OUT = self.addOut('OUT',OUT)

        #signals

    def clock(self):
        if self.Load_Enable.get() == 1:
            self.OUT.prepare(self.Load_data.get())
        else:
            if self.OUT.get() == 32256:# To prevent overflow
                self.OUT.prepare(0)
            else:
                self.OUT.prepare(self.OUT.get()+1)
            
