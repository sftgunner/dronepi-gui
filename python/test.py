from logfile import logevent

# f = open("dronepi.log", "a")
# f.write("[INFO] Test log message")
# f.close()

logevent("Debug log message",0)
logevent("Info log message",1)
logevent("Warning log message",2)
logevent("Error log message",3)
logevent("Fatal log message",4)