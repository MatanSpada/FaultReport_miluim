window.API_BASE = "https://script.google.com/macros/s/AKfycbx9__b4gWg2t9a4_zYR0phfG4rpqAE0_XYpaXhxUfhm_8h9Z0-R4lrVni7_D8AeQ03zNw/exec";
                
window.APARTMENTS = {
    "1": "רותם",
    "2": "דפנה",
    "3": "ארז",
    "4": "אורן",
    "5": "מוריה",
    "6": "זקיף מוריה",
    "7": "אגוז",
    "8": "מלונית אגוז",
    "9": "ורד",
    "10": "מלונית ורד",
    "11": "אקליפטוס",
    "12": "זקיף אקליפטוס"
};

// פונקציית עזר שמחזירה שם מתקן
window.getApartmentName = function(id){
    return window.APARTMENTS[id] || ("מתקן " + id);
};