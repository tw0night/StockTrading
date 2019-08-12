import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import time
import os

TRADING_TIME = [[[9, 0], [15, 20]]]

form_class = uic.loadUiType("pystock.ui")[0]

change_date = False
pr_list = {}
lr_list = {}


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.trade_stocks_done = False

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        fname = "ongoing_list.txt"
        if not os.path.isfile(fname):
            f = open(fname, 'wt')
            f.close()

        # self.get_curclose()
        self.currentTime = datetime.datetime.now()
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)
        # self.get_curclose()

        # 선정 종목 리스트
        self.load_buy_sell_list()

        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accouns_num]

        self.comboBox.addItems(accounts_list)
        self.exe_save = 0
        self.pushButton.clicked.connect(self.save_ongoing)
        self.check_balance()
        # self.kiwoom.OnReceiveRealData.connect(self.kiwoom._receive_real_data)
        self.check_chejan_balance()
        # self.save_final_stock()

        # 주문 들어가는 부분
        self.timer3 = QTimer(self)
        self.timer3.start(1000 * 15)
        self.timer3.timeout.connect(self.timeout3)

        # Timer2 실시간 조회 체크박스 체크하면 10초에 한 번씩 데이터 자동 갱신
        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)

    # 버튼으로 파일 저장
    def save_ongoing(self):
        self.exe_save = 1
        self.check_chejan_balance()

    def is_trading_time(self):
        vals = []
        current_time = self.currentTime.time()
        for start, end in TRADING_TIME:
            start_time = datetime.time(hour=start[0], minute=start[1])
            end_time = datetime.time(hour=end[0], minute=end[1])
            if (current_time >= start_time and current_time <= end_time):
                vals.append(True)
            else:
                vals.append(False)
                pass
        if vals.count(True):
            return True
        else:
            return False

    def is_end_time(self):
        vals = []
        current_time = self.currentTime.time()
        for start, end in TRADING_TIME:
            end_time = datetime.time(hour=end[0], minute=end[1])
            if (current_time == end_time):
                vals.append(True)
            else:
                vals.append(False)
                pass
        if vals.count(True):
            return True
        else:
            return False

    # 자동 주문
    def trade_stocks(self):
        # self.check_balance()
        self.get_curclose()
        auto_buy = []
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        global lr_list
        global pr_list

        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        auto_buy += buy_list
        f.close()

        try:
            f = open("ongoing_list.txt", 'rt')
            buy_list2 = f.readlines()
            auto_buy += buy_list2
            f.close()
        except FileNotFoundError:
            pass

        account = self.comboBox.currentText()
        # close_rate, current_rate = self.get_curclose()
        # print("rate: ", rate[2][0])
        # print(current_rate)
        # buy list

        global change_date

        current_time = datetime.datetime.now()
        correct_time1 = current_time.replace(hour=15, minute=15, second=0, microsecond=0)
        correct_time2 = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
        print(change_date)
        if correct_time1 <= current_time and current_time <= correct_time2 and change_date == True:
            for i in range(len(auto_buy)):
                split_row_data = auto_buy[i].split(';')
                code = split_row_data[0]
                hd = split_row_data[-2]
                if int(hd) > 0:
                    hd = int(hd) - 1
                    print(hd)
                    for i, row_data in enumerate(buy_list):
                        buy_list[i] = buy_list[i].replace(split_row_data[-2], str(hd))
                        print(buy_list[i])
            change_date = False

            f = open("buy_list.txt", 'wt')
            for row_data in buy_list:
                print(row_data)
                f.write(row_data)

        if current_time <= correct_time1 and change_date == False:
            change_date = True

        for i in range(len(auto_buy)):
            split_row_data = auto_buy[i].split(';')
            code = split_row_data[0]
            hoga = split_row_data[1]
            num = split_row_data[2]
            price = split_row_data[3]
            bdr = split_row_data[4]

            print("bdr:", float(bdr))
            # 전날 종가
            new_price = self.true_close[i][0] * float(bdr)
            print("cnt:", i)
            print("rate[cnt]", self.true_close[i][0])
            print("new_price:", new_price)
            hoga = "지정가"

            if split_row_data[-1].rstrip() == '매수전' and new_price <= self.true_current[i][
                0] and self.is_trading_time() == True:
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, int(new_price),
                                       hoga_lookup[hoga], "")
                # 주문이 들어갔을 때만 주문 완료로 바꿈
                if self.kiwoom.orderNum:
                    pass
                    # for i, row_data in enumerate(buy_list):
                print("저장 i", i)
                buy_list[i] = buy_list[i].replace("매수전", "주문완료")
            elif split_row_data[-1].rstrip() == '매수전' and self.is_trading_time() == False:
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")
                # 주문이 들어갔을 때만 주문 완료로 바꿈
                """if self.kiwoom.orderNum:
                    for i, row_data in enumerate(buy_list):
                        buy_list[i] = buy_list[i].replace("매수전", "주문완료")"""

            """if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")
                # 주문이 들어갔을 때만 주문 완료로 바꿈
                if self.kiwoom.orderNum:
                    for i, row_data in enumerate(buy_list):
                        sell_list[i] = sell_list[i].replace("매도전", "판매완료")"""

        num_data = len(self.kiwoom.opw00018_output['multi'])

        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)

        for i in range(num_data):
            code_name = self.kiwoom.opw00018_output['compare'][i][0]
            current_price = self.kiwoom.opw00018_output['compare'][i][2]
            purchase_price = self.kiwoom.opw00018_output['compare'][i][3]
            print("종목이름: %s, 현재가격: %s, 구입가격: %s" % (code_name, current_price, purchase_price))

            location = 0
            while (location < len(current_price)):
                if current_price[location] == ',':
                    current_price = current_price[:location] + current_price[location + 1::]
                location += 1
            current_price = int(current_price)

            location2 = 0
            while (location2 < len(purchase_price)):
                if purchase_price[location2] == ',':
                    purchase_price = purchase_price[:location2] + purchase_price[location2 + 1::]
                location2 += 1

            for j in range(len(auto_buy)):
                split_row_data = auto_buy[j].split(';')
                code = split_row_data[0]
                hoga = split_row_data[1]
                num = split_row_data[2]
                pr = split_row_data[5]
                lr = split_row_data[6]
                hd = split_row_data[-2]
                code_new = self.kiwoom.get_master_code_name(code)

                due_time = current_time.replace(hour=15, minute=10, second=0, microsecond=0)

                if due_time < current_time and hd == "0" and split_row_data[-1].rstrip() == '주문완료':
                    # hoga = "시장가"
                    self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, current_price,
                                           hoga_lookup[hoga], "")
                    if self.kiwoom.orderNum:
                        pass
                    buy_list[j] = buy_list[j].replace("주문완료", "판매완료")
                    print("hd 만료, 시장가 판매")

                if code_name == code_new:
                    print("code name: %s, lr: %f, pr: %f" % (code, float(lr), float(pr)))
                    pr_price = float(pr) * int(purchase_price)
                    print("pr_price: %f * %d = %d" % (float(pr), int(purchase_price), int(pr_price)))
                    lr_price = float(lr) * float(purchase_price)
                    pr_price = int(pr_price)
                    lr_price = int(lr_price)
                    print("profit rate price: ", pr_price)
                    print("loss rate price: ", lr_price)
                    print("current price: ", current_price)

                    if split_row_data[-1].rstrip() == '주문완료' and self.is_trading_time() == True:

                        if (current_price >= pr_price):
                            self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, current_price,
                                                   hoga_lookup[hoga], "")
                            print("pr 주문완료")
                            print(account, code, num, current_price, hoga_lookup[hoga])
                            if self.kiwoom.orderNum:
                                pass
                            buy_list[j] = buy_list[j].replace("주문완료", "판매완료")
                            break


                        elif current_price <= lr_price:
                            self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, current_price,
                                                   hoga_lookup[hoga], "")
                            if self.kiwoom.orderNum:
                                print("lr 주문완료")
                                print(account, code, num, current_price, hoga_lookup[hoga])
                                buy_list[j] = buy_list[j].replace("주문완료", "판매완료")
        print(lr_list)
        print(pr_list)

        # file update
        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

    def load_buy_sell_list(self):
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("ongoing_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        self.num_name = {}
        # buy list
        # j:행, i:열
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            temp_name = split_row_data[0].rstrip()
            # 종목명 구하기
            split_row_data[0] = self.kiwoom.get_master_code_name(split_row_data[0].rstrip())
            self.num_name[split_row_data[0]] = temp_name
            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            temp_name2 = split_row_data[0].rstrip()
            split_row_data[0] = self.kiwoom.get_master_code_name(split_row_data[0].rstrip())
            self.num_name[split_row_data[0]] = temp_name2

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()
        print(self.num_name)

    def save_final_stock(self):
        item_count = len(self.kiwoom.opw00018_output['multi'])
        if (self.is_trading_time() == False):
            self.final_stock = []
            for i in range(item_count):
                row = self.kiwoom.opw00018_output['multi'][i][3]
                self.final_stock.append(row)
            print(self.final_stock)

    def timeout(self):
        market_start_time = QTime(9, 0, 0)
        current_time = QTime.currentTime()
        """if current_time > market_start_time and self.trade_stocks_done is False:
            self.trade_stocks()
            self.trade_stocks_done = True"""

        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def timeout3(self):
        if self.trade_stocks_done == False:
            self.trade_stocks()
        elif self.is_trading_time() == False:
            self.trade_stocks_done = True

    def timeout2(self):
        # if self.checkBox.isChecked():
        self.check_balance()
        self.check_chejan_balance()
        self.load_buy_sell_list()

    def check_chejan_balance(self):
        buy_list = []

        f = open("buy_list.txt", 'rt')
        temp_list = f.readlines()
        buy_list += temp_list
        f.close()
        try:
            f = open("ongoing_list.txt", 'rt')
            onbuy_list = f.readlines()
            buy_list += onbuy_list
            f.close()
        except FileNotFoundError:
            pass

        num = []
        num_new = []
        name = []
        buy_list2 = []
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            name.append(split_row_data[0])
            num.append(split_row_data[2])
        num_new += num
        # SetInputValue(입력 데이터 설정)과 CommRqData(TR 요청)
        # 최대 20개의 보유 종목 데이터 리턴 반복
        self.kiwoom.reset_opt10075_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opt10075_req", "opt10075", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opt10075_req", "opt10075", 0, "2000")
            # if self.is_trading_time() == False:
            #    break

        item_count = len(self.kiwoom.opt10075_output['no_che'])
        self.tableWidget_4.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opt10075_output['no_che'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_4.setItem(j, i, item)
                if self.is_end_time() == True or self.is_trading_time() == False or self.exe_save == 1:
                    if row[0] == '체결':
                        # print(self.kiwoom.opt10075_output['no_che'][j])
                        if row[1] == '+매수':
                            # if row[1] == '-매도':
                            for l in range(0, j + 1):
                                if self.kiwoom.opt10075_output['no_che'][l][3] == \
                                        self.kiwoom.opt10075_output['no_che'][j][3]:
                                    # print("l-{0} {1}".format(l, self.kiwoom.opt10075_output['no_che'][l]))
                                    # print("j-{0} {1}".format(j, self.kiwoom.opt10075_output['no_che'][j]))
                                    if not self.kiwoom.opt10075_output['no_che'][l][1] == '-매도':
                                        for k in range(len(buy_list)):
                                            if int(self.num_name[self.kiwoom.opt10075_output['no_che'][j][3]]) == int(
                                                    name[k]):
                                                buy_list2.append(buy_list[k])
                                # print(self.kiwoom.opt10075_output['no_che'][j][3])
                                # print("l - %d, j - %d" %(l, j))
                                # print("확인용", self.kiwoom.opt10075_output['no_che'][l])
                            """for k in range(len(buy_list)):
                                if int(self.num_name[row[3]]) == int(name[k]):
                                    #print(k)
                                    #print(buy_list[k])
                                    buy_list2.append(buy_list[k])"""
        buy_list2 = list(set(buy_list2))
        if self.is_end_time() == True or self.is_trading_time() == False or self.exe_save == 1:
            f = open("ongoing_list.txt", 'wt')
            for row_data in buy_list2:
                row_data = row_data.replace('매수전', '주문완료')
                f.write(row_data)
            f.close()

        self.exe_save == 0
        self.tableWidget_4.resizeRowsToContents()

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001
        # 예수금 데이터 얻어오기
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        # 예수금 데이터 tableWidget에 출력
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        # 해당 칼럼에 값 추가
        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        # 아이템 크기에 맞춰 행 높이 조절
        self.tableWidget.resizeRowsToContents()

        # Item list 보유종목 출력
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            if row[0] in lr_list and pr_list:
                str_lr = str(lr_list[row[0]])
                row[4] = str_lr
                print(row[4])
                str_pr = str(pr_list[row[0]])
                row[5] = str_pr
                print(row[5])
            print(row)
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)
        self.tableWidget_2.resizeRowsToContents()

    # 종가와 시가를 받아오기 위한 함수
    def get_ohlcv(self, code, start):
        self.kiwoom.ohlcv = {'date': [], 'close': []}
        self.kiwoom.final = {'close': []}
        self.kiwoom.current = {'current': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

    def get_curclose(self):
        self.true_close = []
        self.true_current = []
        self.code = []
        self.buy_list = []
        today = datetime.datetime.today().strftime("%Y%m%d")
        f = open("buy_list.txt", 'rt')
        temp_list = f.readlines()
        self.buy_list += temp_list

        try:
            f = open("ongoing_list.txt", 'rt')
            onbuy_list = f.readlines()
            self.buy_list += onbuy_list
        except FileNotFoundError:
            pass

        for row_data in self.buy_list:
            split_row_data = row_data.split(';')
            self.code.append(split_row_data[0])
        # 현재 시가과 전날 종가를 받아옴
        for i in range(len(self.code)):
            print("code: ", self.code[i])
            self.get_ohlcv(self.code[i], today)
            self.true_close.append(self.kiwoom.final['close'])
            self.true_current.append(self.kiwoom.current['current'])
        print(self.true_close)

        f.close()
        # return (true_close, true_current)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()