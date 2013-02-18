import wx
from wx.lib.agw import ultimatelistctrl as ULC
 
########################################################################
class TestPanel(wx.Panel):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)
 
        font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldfont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldfont.SetWeight(wx.BOLD)
        boldfont.SetPointSize(12)
 
        self.ultimateList = ULC.UltimateListCtrl(self, agwStyle = wx.LC_REPORT
                                         | wx.LC_VRULES
                                         | wx.LC_HRULES)
 
        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_CHECK
        info._image = []
        info._format = 0
        info._kind = 1
        info._text = "Artist Name"
        self.ultimateList.InsertColumnInfo(0, info)
 
        info = ULC.UltimateListItem()
        info._format = wx.LIST_FORMAT_RIGHT
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._image = []
        info._text = "Title"
        info._font = boldfont
        self.ultimateList.InsertColumnInfo(1, info)
 
        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info._format = 0
        info._text = "Genre"
        info._font = font
        info._image = []
        self.ultimateList.InsertColumnInfo(2, info)
 
        self.ultimateList.InsertStringItem(0, "Newsboys")
        self.ultimateList.SetStringItem(0, 1, "Go")
        self.ultimateList.SetStringItem(0, 2, "Rock")
 
        self.ultimateList.InsertStringItem(1, "Puffy")
        self.ultimateList.SetStringItem(1, 1, "Bring It!")
        self.ultimateList.SetStringItem(1, 2, "Pop")
 
        self.ultimateList.InsertStringItem(2, "Family Force 5")
        self.ultimateList.SetStringItem(2, 1, "III")
        self.ultimateList.SetStringItem(2, 2, "Crunk")
 
        self.ultimateList.SetColumnWidth(0, 150)
        self.ultimateList.SetColumnWidth(1, 200)
        self.ultimateList.SetColumnWidth(2, 100)
 
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ultimateList, 1, wx.EXPAND)
        self.SetSizer(sizer)
 
########################################################################
class TestFrame(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="MvP UltimateListCtrl Demo")
        panel = TestPanel(self)
        self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)
    frame = TestFrame()
    app.MainLoop()