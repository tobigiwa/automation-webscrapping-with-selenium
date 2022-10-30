import os


# class start
class GlobalVariable:

    # to store key value pairs of months key=string, value=no. of month
    months = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07",
                "August": "08", "September": "09", "October": "10", "November": "11", "December": "12", "JANUARY": "01",
                "FEBRUARY": "02", "MARCH": "03", "APRIL": "04", "MAY": "05", "JUNE": "06", "JULY": "07","AUGUST": "08",
                "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11", "DECEMBER": "12", "january": "01", "february": "02", "march": "03", "april": "04", "may": "05", "june": "06", "july": "07",
                "august": "08", "september": "09", "october": "10", "november": "11", "december": "12", "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06", "JUL": "07","AUG": "08",
                "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12", "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                "May": "05", "Jun": "06", "Jul": "07","Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12", "jan": "01", "feb": "02", "mar": "03", "apr": "04",
                "may": "05", "jun": "06", "jul": "07","aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}
    
    states_abv_dict = {'al' : 'USA', 'ak' : 'USA', 'az' : 'USA', 'ar' : 'USA', 'ca' : 'USA', 'co' : 'USA',
                        'ct' : 'USA', 'de' : 'USA', 'fl' : 'USA', 'ga' : 'USA', 'hi' : 'USA', 'id' : 'USA',
                        'il' : 'USA', 'in' : 'USA', 'ia' : 'USA', 'ks' : 'USA', 'ky' : 'USA', 'la' : 'USA',
                        'me' : 'USA', 'md' : 'USA', 'ma' : 'USA', 'mi' : 'USA', 'mn' : 'USA', 'ms' : 'USA',
                        'mo' : 'USA', 'mt' : 'USA', 'ne' : 'USA', 'nv' : 'USA', 'nh' : 'USA', 'nj' : 'USA',
                        'nm' : 'USA', 'ny' : 'USA', 'nc' : 'USA', 'nd' : 'USA', 'oh' : 'USA', 'ok' : 'USA',
                        'or' : 'USA', 'pa' : 'USA', 'ri' : 'USA', 'sc' : 'USA', 'sd' : 'USA', 'tn' : 'USA',
                        'tx' : 'USA', 'ut' : 'USA', 'vt' : 'USA', 'va' : 'USA', 'wa' : 'USA', 'wv' : 'USA',
                        'wi' : 'USA', 'wy' : 'USA'}
    
    states_dict = {'alabama' : 'USA', 'alaska' : 'USA', 'arizona' : 'USA', 'arkansas' : 'USA', 'california' : 'USA', 'colorado' : 'USA', 'connecticut' : 'USA',
                    'delaware' : 'USA', 'florida' : 'USA', 'georgia' : 'USA', 'hawaii' : 'USA', 'idaho' : 'USA', 'illinois' : 'USA', 'indiana' : 'USA', 'iowa' : 'USA',
                    'kansas' : 'USA', 'kentucky' : 'USA', 'louisiana' : 'USA', 'maine' : 'USA', 'maryland' : 'USA', 'massachusetts' : 'USA', 'michigan' : 'USA', 'minnesota' : 'USA',
                    'mississippi' : 'USA', 'missouri' : 'USA', 'montana' : 'USA', 'nebraska' : 'USA', 'nevada' : 'USA', 'new hampshire' : 'USA', 'new jersey' : 'USA', 'new mexico' : 'USA',
                    'new york' : 'USA', 'north carolina' : 'USA', 'north dakota' : 'USA', 'ohio' : 'USA', 'oklahoma' : 'USA', 'oregon' : 'USA', 'pennsylvania' : 'USA', 'rhode island' : 'USA',
                    'south carolina' : 'USA', 'south dakota' : 'USA', 'tennessee' : 'USA', 'texas' : 'USA', 'utah' : 'USA', 'vermont' : 'USA', 'virginia' : 'USA', 'washington' : 'USA', 'west virginia' : 'USA',
                    'wisconsin' : 'USA', 'wyoming' : 'USA'}

    # LibraryFilePath="/home/indiamart/public_html/parsing/global-files/"
    ChromeDriverPath= os.path.join(os.getcwd(), 'chromedriver')  #path of chromedriver
    TsvFilePath= os.path.join(os.getcwd(), 'tsv-files/')    # path for temp files

# class end
