from datetime import datetime
import serial
import re


class dBSensor:

    def __init__(self, path, list_of_measures, valid_ranges, description, fs):
        self.header = list_of_measures  # Liste der gemessenen Sensorwerte
        self.current_values = []  # Sensorwerte
        self.valid_ranges = valid_ranges  # Wertebereich
        self.fs = 1  # Samplingfrequenz
        self.health = None  # Sensor noch i.O.?
        self.init_time = datetime.now()  # Initialisierungszeitpunkt
        self.last_value_received = datetime.now()
        self.description = description
        self.logging = True
        self.path = path
        self.connection = None
        self.connected = False

    def receive(self):
        while True:
            new_values = None
            while new_values is None:
                self.check_health()
                try:
                    new_line = self.connection.readline()
                    new_values = self.parse_input(new_line)
                except Exception as e:
                    print(e)
                    pass
            self.current_values = new_values
            self.last_value_received = datetime.now()

            if self.logging:
                print(self.last_value_received.strftime("%H:%M:%S") + " received:" + str(self.current_values))

    def connect(self):
        try:
            with serial.Serial(self.path) as self.connection:
                self.connection.reset_input_buffer()
                self.connected = True
                self.receive()
        except Exception as e:
            print("Verbindung von" + self.description + "unter" + self.path + "konnte nicht hergestellt werden wegen:" + str(e))

    def parse_input(self):
        return None

    def print(self):
        print(self.header)
        print(self.values)

    def check_health(self):
        if (datetime.now() - self.last_value_received).seconds > 1 / self.fs:
            self.health = "Underflow"
            if self.logging:
                print("Underflow")



class dBWXT5xx(dBSensor):

    def __init__(self):
        self.lastR1 = None
        super().__init__( "/dev/virtualcom0", ["T", "rF", "Ld", "Wr", "Wg", "R"],
                         [[-20, 50], [0, 100], [800, 1100], [0, 360], [0, 20], [False, True]],
                         "Meteorologiesensor Vaisala WXT5xx",1)
        self.connect()

    def parse_input(self,new_line):
        nl = [f.split("=") for f in new_line.decode("UTF-8").split(",")]
        line_type = nl[0][0]
        match line_type:
            case "0R1":
                self.lastR1 = nl
                return None
            case "0R2":
                if self.lastR1 is not None:
                    nl1 = self.lastR1
                    self.lastR1 = None
                    parsed_data = []
                    for item in nl1[1:]:
                        parsed_data.append(re.sub('[^\d\.]','', item[1]))
                    for item in nl[1:]:
                        parsed_data.append(re.sub('[^\d\.]','', item[1]))

                    return list(map(float, parsed_data))




Vaisala = dBWXT5xx()
