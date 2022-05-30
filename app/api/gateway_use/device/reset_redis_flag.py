import redis

r = redis.Redis('localhost')
serial_isOpen = r.get('serial.isOpen')
print('Now serial.isOpen:', serial_isOpen)

r.set('serial.isOpen', '0')
serial_isOpen = r.get('serial.isOpen')
print('After serial.isOpen:', serial_isOpen)
