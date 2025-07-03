class Tag:

    """Placeholder class for Tags 
    """

    def __init__(self,uid,model,x,y,z):
        self.position = [x,y,z]
        self.uid = uid
        self.model = model
        self.power = 0
        self.gain = 0 
        self.resistance = 0

    
    def to_dict(self):
        """For placing tags into dicts correctly on JSON
        """
        return{'model':self.model,'x':self.position[0], 'y':self.position[1], 'z':self.position[2]}
    
    @classmethod
    def from_dict(cls,uid,data):
        """Creates a tag object from a JSON input

        Args:
            uid (string): Unique identifier for tag
            data (list): list of Coordinates

        Returns:
            tag: returns tag loaded from JSON
        """
        return cls(uid,data['model'],data['x'],data['y'],data['z'])