from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QPainter
from PyQt5 import QtChart
from PyQt5.QtWidgets import *
import sys
from ui.table_model import CustomTableModel
from scrap.dart.finance_sheet import FinanceSheetAdapter
from scrap.krx.stock_code import StockCode

'''
https://stackoverflow.com/questions/58274166/cannot-import-pyqtchart-in-python-3-7
pyqt5에서 QtChart를 사용하기 위해서는 아래 패키지를 설치해주어야한다.
python -m pip install PyQt5==5.13 PyQtChart==5.13
그리고 import할 때에는 아래 처럼 해주어야 한다.
from PyQt5 import QtChart
'''

class Widget(QWidget):
    # def __init__(self, data):
    def __init__(self):
        QWidget.__init__(self)

        self.grp_box = QGroupBox("재무 정보")
        # Create Widgets
        self.label_stock_code_search = QLabel("종목 코드 조회:")
        self.edit_corp_name = QLineEdit("회사명을 입력하고 엔터를 입력하세요.")
        self.edit_corp_code = QLineEdit("종목 코드:")
        self.btn_start = QPushButton("dart api 초기화")
        self.status_label = QLabel("진행 상태:")
        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.status_label.setAlignment(Qt.AlignLeft)
        self.btn_update_fss_dart = QPushButton("재무 정보 수집")
        self.edit_corp_name.returnPressed.connect(self.update_codes)
        self.btn_start.clicked.connect(self.init_fss_dart)
        self.btn_update_fss_dart.clicked.connect(self.update_fss_dart)


        # Getting the Model - PER, PBR, EPS, ROE를 table로
        # self.model = CustomTableModel(data)
        self.model = CustomTableModel()
        # Creating a QTableView
        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        self.left_inner_layout = QVBoxLayout()
        self.left_inner_layout.addWidget(self.label_stock_code_search)
        self.left_inner_layout.addWidget(self.edit_corp_name)
        self.left_inner_layout.addWidget(self.edit_corp_code)
        self.left_inner_layout.addWidget(self.btn_start)
        self.left_inner_layout.addWidget(self.status_label)
        self.left_inner_layout.addWidget(self.pbar)
        self.left_inner_layout.addWidget(self.btn_update_fss_dart)
        self.left_inner_layout.setAlignment(Qt.AlignTop)
        self.grp_box.setLayout(self.left_inner_layout)

        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.grp_box)

        # Right Layout - # Creating QChartView: 매출액, 순이익, 자산 증가 추세
        self.chart = QtChart.QChart()
        self.chart.setAnimationOptions(QtChart.QChart.AllAnimations)
        self.add_series("Magnitude (Column 1)", [0, 1])
        self.chart_view = QtChart.QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        # Right Layout
        self.right_layout = QVBoxLayout()
        # size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # size.setHorizontalStretch(4)
        # self.chart_view.setSizePolicy(size)
        self.right_layout.addWidget(self.chart_view)

        # QWidget Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)

        # Set the layout to the QWidget
        self.setLayout(self.main_layout)
        
    # Greets the user
    def get_code_text(self):
        print("종목 정보 %s" % self.edit_corp_name.text())
    
    def init_fss_dart(self):
        print("init_fss_dart")
        str_name = self.str_name
        str_code = self.str_code
        self.pbar.setValue(0)
        self.finance_sheet = FinanceSheetAdapter(str_name, str_code)
        self.pbar.setValue(30)
        self.finance_sheet.get_corp_list()
        self.pbar.setValue(60)
        self.finance_sheet.get_finance_sheet()
        self.pbar.setValue(100)

    def update_codes(self):
        self.stock_code = StockCode()
        self.stock_code.update_stock_codes()
        try:
            self.str_name = self.edit_corp_name.text()
            code = self.stock_code.get_stock_code_by_name(self.str_name)#edit_corp_name
            print("stock_code : {}".format(code))
            self.str_code = '%06d'%code
            self.edit_corp_code.setText(self.str_code)
            
        except ValueError:
            print("invalid corp name: {}".format(self.edit_corp_name.text()))
            self.edit_corp_code.setText("잘못된 회사명입니다.")
    
    def update_fss_dart(self):
        print("update_fss_dart")
        # self.finance_sheet.update_finance_sheet_all()
        self.finance_sheet.update_consolidated_income_statement()
        # TODO: dart dataframe에서 필요한 부분만 dataframe으로 정제하고,
        # table_model에 넘겨서 table 모델로 변환, table view에 출력

    def add_series(self, name, columns):
        # Create QLineSeries
        self.series = QtChart.QLineSeries()
        self.series.setName(name)

        # Filling QLineSeries
        for i in range(self.model.rowCount()):
            # Getting the data
            t = self.model.index(i, 0).data()
            date_fmt = "yyyy-MM-dd HH:mm:ss.zzz"

            x = QDateTime().fromString(t, date_fmt).toSecsSinceEpoch()
            y = float(self.model.index(i, 1).data())

            if x > 0 and y >0:
                self.series.append(x, y)
            
        self.chart.addSeries(self.series)

        # Setting X-axis
        self.axis_x = QtChart.QDateTimeAxis()
        self.axis_x.setTickCount(10)
        self.axis_x.setFormat("dd.MM (h:mm)")
        self.axis_x.setTitleText("Date")
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.series.attachAxis(self.axis_x)

        # Setting Y-axis
        self.axis_y = QtChart.QValueAxis()
        self.axis_y.setTickCount(10)
        self.axis_y.setLabelFormat("%.2f")
        self.axis_y.setTitleText("Magnitude")
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_y)

        # Getting the color from QChart to use it on the QTableView
        self.model.color = "{}".format(self.series.pen().color().name())
