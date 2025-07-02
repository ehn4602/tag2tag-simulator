class Tag:

    """Placeholder class for Tags 
    """

    def __init__(self,uid,x,y,z):
        self.x = x
        self.y = y
        self.z = z
        self.uid = uid

    
    def to_dict(self):
        """For placing tags into dicts correctly on JSON
        """
        return{'x':self.x, 'y':self.y, 'z':self.z}
    
    @classmethod
    def from_dict(cls,uid,data):
        """Creates a tag object from a JSON input

        Args:
            uid (string): Unique identifier for tag
            data (list): list of Coordinates

        Returns:
            tag: returns tag loaded from JSON
        """
        return cls(uid,data['x'],data['y'],data['z'])