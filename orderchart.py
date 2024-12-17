import matplotlib.pyplot as plt

class OrderChart:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.buy_limit_price, = self.ax.plot([], [], label='Buy Limit Price')
        self.sell_limit_price, = self.ax.plot([], [], label='Sell Limit Price')
        self.last_price, = self.ax.plot([], [], label='Last Price')
        self.ax.legend()
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Price')
        self.times = []
        self.buy_prices = []
        self.sell_prices = []
        self.last_prices = []

    def update(self, time, buy_price, sell_price, last_price):
        print(time, buy_price, sell_price, last_price)
        self.times.append(time)
        self.buy_prices.append(float(buy_price))
        self.sell_prices.append(float(sell_price))
        self.last_prices.append(float(last_price))
        
        self.buy_limit_price.set_data(self.times, self.buy_prices)
        self.sell_limit_price.set_data(self.times, self.sell_prices)
        self.last_price.set_data(self.times, self.last_prices)
        
        self.ax.relim()
        self.ax.autoscale_view()
        plt.draw()
        plt.pause(0.01)


if __name__ == '__main__':
    import time
    import random
    order_chart = OrderChart()
    for i in range(100):
        order_chart.update(i, random.randint(1, 100), random.randint(1, 100), random.randint(1, 100))
        time.sleep(0.1)
    plt.show()