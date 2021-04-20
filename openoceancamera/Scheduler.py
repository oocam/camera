from datetime import date, datetime, timezone


class Scheduler(object):
    def __init__(self):
        self.schedule_data  = []

    def should_start(self):
        for i in range(len(self.schedule_data)):
            if (
                self.schedule_data[i]["start"]
                <= datetime.now()
                <= self.schedule_data[i]["stop"]
            ):
                return i
        return -1

    def get_slot(self, index):
        return self.schedule_data[index]

    def load_scheduler_data(self, data):
        self.schedule_data = []
        for slot in data:
            frame = {}
            frame["start"] = datetime.strptime(slot["start"], "%Y-%m-%d-%H:%M:%S")
            frame["stop"] = datetime.strptime(slot["stop"], "%Y-%m-%d-%H:%M:%S")
            frame["iso"] = slot.get("iso", 0)
            frame["frequency"] = slot.get("frequency", 10)
            frame["shutter_speed"] = slot.get("shutter_speed", 0)
            frame["video"] = slot.get("video")
            frame["upload"] = slot.get("upload", False)
            frame["light"] = slot.get("light", 0)
            frame["wiper"] = slot.get("wiper", False)
            frame["exposure_mode"] = slot.get("exposure_mode", "auto")
            frame["exposure_compensation"] = slot.get("exposure_compensation", 0)
            frame["framerate"] = slot.get("framerate", 0)
            resolution = slot.get("resolution", {"x": 1920, "y": 1080})
            frame["resolution"]= (resolution["x"], resolution["y"])
            self.schedule_data.append(frame.copy())

    def next_future_timeslot(self):
        future_slots = []
        # Get the future slots
        for slot in self.schedule_data:
            if slot["start"] >= datetime.now():
                future_slots.append(slot)
        # Sorts the slots in case they may not be
        future_slots = sorted(future_slots, key=lambda x: x["start"])
        if len(future_slots):
            return future_slots[0]
        else:
            return None
    
    def time_to_nearest_schedule(self):
        possible_slots = []
        # Get the future slots
        for slot in self.schedule_data:
            if slot["start"] >= datetime.now():
                possible_slots.append(slot)

        # Sorts the slots in case they may not be
        possible_slots = sorted(possible_slots, key=lambda x: x["start"])
        # Take the difference between the most recent slot's start time and time now
        delta = possible_slots[0]["start"] - datetime.now()
        return int(delta.total_seconds())

    def time_to_slot(self, slot):
        delta = slot["start"] - datetime.now()
        return int(delta.total_seconds())
