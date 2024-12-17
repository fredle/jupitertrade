import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

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

        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        plt.ion()

    def animate(self, _):
        self.buy_limit_price.set_data(self.times, self.buy_prices)
        self.sell_limit_price.set_data(self.times, self.sell_prices)
        self.last_price.set_data(self.times, self.last_prices)
        
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        
    def update(self, time, buy_price, sell_price, last_price):

        self.times.append(time)
        self.buy_prices.append(float(buy_price))
        self.sell_prices.append(float(sell_price))
        self.last_prices.append(float(last_price))
        
        self.buy_limit_price.set_data(self.times, self.buy_prices)
        self.sell_limit_price.set_data(self.times, self.sell_prices)
        self.last_price.set_data(self.times, self.last_prices)
        
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()



if __name__ == '__main__':
    import random
    import time

    order_chart = OrderChart()
    
    while True:
        order_chart.update(time.time(), random.uniform(100, 200), random.uniform(100, 200), random.uniform(100, 200))
        plt.pause(1)
