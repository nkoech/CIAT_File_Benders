import os, json, sys, arcpy
from arcpy import env
from arcpy import da
from collections import Counter

class FClasssCreator(object):
    """
    Go through several land use/cover classes in a feature class and create new feature classes
    from polygons with areas between certain range
    
    Author: Koech Nicholas
    Year: 2014
    """

    def get_json_file(self):
        """Get the current directory and search for a json file"""
        cwd = os.getcwd()
        status = "FALSE"
        for file in os.listdir(cwd):
            if file.endswith(".json"):
                status = "TRUE"
                file_path = os.path.join(cwd, file).replace("\\","/")
                return file_path
        if status == "FALSE":
            print "Parameter file(.json) file not found"

    def get_json_keys(self):
        """Reads json file and returns keys"""
        try:
            jCont = json.loads(open(self.get_json_file()).read()) #read and load a json file
        except ValueError:
            print "Your file " + self.get_json_file() + " is not a valid json file"
        in_Feature = self.loop_json(jCont, "input_Feature", "in_Feature") 
        out_loc = self.loop_json(jCont, "output_Location", "out_loc")
        gt = self.loop_json(jCont, "greater_than", "gt")
        lt = self.loop_json(jCont, "less_than", "lt")
        cls_field = self.loop_json(jCont, "class_Field", "cls_field")
        wrk_pace = self.loop_json(jCont, "workspace", "wrk_pace")
        area = self.loop_json(jCont, "area_Field", "area")
        return (in_Feature, out_loc, gt, lt, cls_field, wrk_pace, area)

    def loop_json(self, jCont, outerKey, innerKey):
        """Get contents from a Json file"""
        for key in jCont[outerKey]: #loop through json keys
            jValue = key[innerKey] #get directory location
        return jValue

    def set_workspace(self):
        """Sets the ArcGIS environment workspace"""
        try:
            env.workspace = self.get_json_keys()[5]
            env.overwriteOutput = True
        except arcpy.ExecuteError:
            print arcpy.GetMessages(2)
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            print e.args[0]
            arcpy.AddError(e.args[0])

    def get_classes(self):
        """Get the number of classes in the shapefile"""
        row_val = []
        with da.SearchCursor(self.get_json_keys()[0],[self.get_json_keys()[4]]) as sc: #search on the class field
            print "Wait... calculating number of classes"
            for row in sc:
                row_val.append(int(row[0]))
        return max(row_val)            

    def create_featureCls(self):
        """Create feature class from group of classes"""
        try:            
            delmtField1 = arcpy.AddFieldDelimiters(env.workspace, self.get_json_keys()[4]) # get field delimiter
            delmtField2 = arcpy.AddFieldDelimiters(env.workspace, self.get_json_keys()[6])            
            num_classes = self.get_classes()
            counter = 1
            while (counter < num_classes):
                feature_name = "Output_" + str(counter) + ".shp" # feature class output
                # where clause expression
                expression = delmtField1 + " = " + str(counter) + " and " + "(" + delmtField2 + " >= " + self.get_json_keys()[2] + " AND " + delmtField2 + " <= " + self.get_json_keys()[3] +")"
                print "Wait... creating " + feature_name             
                arcpy.FeatureClassToFeatureClass_conversion(self.get_json_keys()[0], self.get_json_keys()[1], feature_name, expression)#create feature classes
                counter = counter + 1
            print "New feature classes successfully created!!!"
        except arcpy.ExecuteError:
            print arcpy.GetMessages(2)
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            print e.args[0]
            arcpy.AddError(e.args[0])
            
def main():
    """Main program"""
    fCreator = FClasssCreator()
    fCreator.set_workspace()
    fCreator.create_featureCls()

if __name__ == "__main__":
    main()
    
        
        
    


