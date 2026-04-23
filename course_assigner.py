# course_assigner.py

from collections import defaultdict

# ============================================================
#  GLOBAL COURSE CATALOG (FULL GLOBAL CATALOG)
# ============================================================

COURSE_CATALOG = {
    "USA": {
        "Math": {
            "high_school": [
                "General Math", "Mathematics", "Integrated Math",
                "Integrated Math I", "Integrated Math II", "Integrated Math III",
                "Algebra I", "Geometry", "Algebra II",
                "Trigonometry", "Pre-Calculus", "Honors Pre-Calculus",
                "Functions & Relations",
                "AP Calculus AB", "AP Calculus BC", "AP Statistics"
            ],
            "college": [
                "College Algebra", "Multivariable Calculus", "Linear Algebra",
                "Differential Equations", "Discrete Mathematics",
                "Probability Theory", "Mathematical Statistics"
            ]
        },
        "Science": {
            "high_school": [
                "General Science", "Integrated Science", "Physical Science", "Life Science",
                "Biology", "Honors Biology", "AP Biology",
                "Chemistry", "Honors Chemistry", "AP Chemistry",
                "Physics", "Honors Physics",
                "AP Physics 1", "AP Physics 2",
                "AP Physics C: Mechanics", "AP Physics C: Electricity & Magnetism",
                "Environmental Science", "AP Environmental Science",
                "Earth Science", "Marine Science"
            ],
            "college": [
                "General Biology I", "General Biology II",
                "General Chemistry I", "General Chemistry II",
                "Organic Chemistry I", "Organic Chemistry II",
                "Physics I (Mechanics)", "Physics II (Electricity & Magnetism)",
                "Cell Biology", "Genetics", "Biochemistry",
                "Environmental Science (College)", "Microbiology"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "English 9", "English 10", "English 11", "English 12",
                "English Language Arts (ELA)",
                "AP English Language", "AP English Literature"
            ],
            "college": [
                "College Composition", "Advanced Composition",
                "Literary Analysis", "Creative Writing",
                "Rhetoric and Writing", "World Literature"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "World History", "US History", "European History",
                "Government", "Civics", "Geography",
                "Economics", "Psychology", "Sociology",
                "AP World History", "AP US History", "AP European History",
                "AP Microeconomics", "AP Macroeconomics"
            ],
            "college": [
                "World History (College)", "US History (College)",
                "Political Science", "International Relations",
                "Sociology", "Psychology", "Macroeconomics",
                "Microeconomics", "Philosophy"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "Computer Science", "Information Technology", "Programming",
                "Web Development", "Software Development",
                "AP Computer Science A", "AP Computer Science Principles",
                "Robotics", "Data Science"
            ],
            "college": [
                "Introduction to Computer Science",
                "Data Structures and Algorithms",
                "Operating Systems", "Databases",
                "Computer Networks", "Software Engineering",
                "Artificial Intelligence", "Machine Learning"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "Business Studies", "Accounting", "Finance", "Marketing",
                "Entrepreneurship", "Economics",
                "AP Microeconomics", "AP Macroeconomics"
            ],
            "college": [
                "Introduction to Business", "Financial Accounting",
                "Managerial Accounting", "Principles of Marketing",
                "Corporate Finance", "Business Law"
            ]
        },
        "Arts": {
            "high_school": [
                "Visual Arts", "Fine Arts", "Music", "Drama", "Theatre",
                "Photography", "Graphic Design", "Digital Media",
                "AP Art & Design"
            ],
            "college": [
                "Drawing I", "Painting I", "Digital Art",
                "Graphic Design (College)", "Art History",
                "Film Studies", "Music Theory (College)"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Spanish", "French", "German", "Mandarin", "Arabic",
                "Japanese", "Korean", "Latin",
                "AP Spanish", "AP French"
            ],
            "college": [
                "Intermediate Spanish", "Advanced Spanish",
                "Intermediate French", "Advanced French",
                "Linguistics"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "Physical Education", "Health", "Sports Science",
                "Fitness", "Yoga"
            ],
            "college": [
                "Exercise Physiology", "Kinesiology",
                "Sports Psychology", "Nutrition"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies", "Special Topics"]
        }
    },

    "IB": {
        "Math": {
            "high_school": [
                "IB Math AA SL", "IB Math AA HL",
                "IB Math AI SL", "IB Math AI HL"
            ],
            "college": [
                "Calculus I", "Linear Algebra", "Discrete Mathematics"
            ]
        },
        "Science": {
            "high_school": [
                "IB Biology SL", "IB Biology HL",
                "IB Chemistry SL", "IB Chemistry HL",
                "IB Physics SL", "IB Physics HL",
                "IB Environmental Systems and Societies"
            ],
            "college": [
                "General Biology I", "General Chemistry I",
                "Physics I (Mechanics)"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "IB English A: Language & Literature SL",
                "IB English A: Language & Literature HL",
                "IB English A: Literature SL",
                "IB English A: Literature HL"
            ],
            "college": [
                "Literary Analysis", "World Literature"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "IB History SL", "IB History HL",
                "IB Economics SL", "IB Economics HL",
                "IB Psychology SL", "IB Psychology HL"
            ],
            "college": [
                "International Relations", "Macroeconomics", "Microeconomics"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "IB Computer Science SL", "IB Computer Science HL"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "IB Business Management SL", "IB Business Management HL"
            ],
            "college": [
                "Introduction to Business", "Corporate Finance"
            ]
        },
        "Arts": {
            "high_school": [
                "IB Visual Arts SL", "IB Visual Arts HL",
                "IB Music SL", "IB Music HL",
                "IB Theatre SL", "IB Theatre HL"
            ],
            "college": [
                "Art History", "Film Studies"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "IB Language B SL", "IB Language B HL"
            ],
            "college": [
                "Intermediate Language Studies"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "IB Sports, Exercise & Health Science"
            ],
            "college": [
                "Exercise Physiology"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "UK": {
        "Math": {
            "high_school": [
                "GCSE Mathematics",
                "A-Level Mathematics", "A-Level Further Mathematics"
            ],
            "college": [
                "Calculus I", "Linear Algebra"
            ]
        },
        "Science": {
            "high_school": [
                "GCSE Biology", "GCSE Chemistry", "GCSE Physics",
                "A-Level Biology", "A-Level Chemistry", "A-Level Physics"
            ],
            "college": [
                "General Biology I", "General Chemistry I", "Physics I (Mechanics)"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "GCSE English Language", "GCSE English Literature",
                "A-Level English Language", "A-Level English Literature"
            ],
            "college": [
                "Literary Analysis"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "GCSE History", "GCSE Geography",
                "A-Level History", "A-Level Geography",
                "A-Level Economics"
            ],
            "college": [
                "World History (College)", "Economics"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "GCSE Computer Science", "A-Level Computer Science"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "GCSE Business Studies", "A-Level Business Studies",
                "A-Level Accounting", "A-Level Economics"
            ],
            "college": [
                "Financial Accounting", "Principles of Marketing"
            ]
        },
        "Arts": {
            "high_school": [
                "GCSE Art & Design", "A-Level Art & Design",
                "GCSE Music", "A-Level Music"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "GCSE French", "GCSE Spanish", "GCSE German",
                "A-Level French", "A-Level Spanish", "A-Level German"
            ],
            "college": [
                "Intermediate French", "Intermediate Spanish"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "GCSE Physical Education", "A-Level Physical Education"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "CAMBRIDGE": {
        "Math": {
            "high_school": [
                "Cambridge IGCSE Mathematics",
                "Cambridge Additional Mathematics",
                "A-Level Mathematics", "A-Level Further Mathematics"
            ],
            "college": [
                "Calculus I", "Linear Algebra"
            ]
        },
        "Science": {
            "high_school": [
                "Cambridge IGCSE Biology",
                "Cambridge IGCSE Chemistry",
                "Cambridge IGCSE Physics",
                "A-Level Biology", "A-Level Chemistry", "A-Level Physics"
            ],
            "college": [
                "General Biology I", "General Chemistry I", "Physics I (Mechanics)"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "Cambridge IGCSE English",
                "Cambridge IGCSE Literature"
            ],
            "college": [
                "World Literature"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "Cambridge IGCSE History",
                "Cambridge IGCSE Geography"
            ],
            "college": [
                "World History (College)"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "Cambridge IGCSE Computer Science"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "Cambridge IGCSE Business Studies",
                "Cambridge IGCSE Accounting"
            ],
            "college": [
                "Financial Accounting"
            ]
        },
        "Arts": {
            "high_school": [
                "Cambridge IGCSE Art & Design"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Cambridge IGCSE Languages"
            ],
            "college": [
                "Intermediate Language Studies"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "Cambridge IGCSE Physical Education"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "CBSE": {
        "Math": {
            "high_school": [
                "CBSE Mathematics", "Applied Mathematics", "Additional Mathematics"
            ],
            "college": [
                "Engineering Mathematics I", "Engineering Mathematics II"
            ]
        },
        "Science": {
            "high_school": [
                "CBSE Physics", "CBSE Chemistry", "CBSE Biology",
                "CBSE Science"
            ],
            "college": [
                "Physics I (Mechanics)", "General Chemistry I", "General Biology I"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "CBSE English"
            ],
            "college": [
                "College Composition"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "CBSE Social Science"
            ],
            "college": [
                "Economics", "Political Science"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "CBSE Computer Applications", "CBSE Informatics Practices"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "CBSE Business Studies", "CBSE Accountancy", "CBSE Economics"
            ],
            "college": [
                "Financial Accounting", "Principles of Marketing"
            ]
        },
        "Arts": {
            "high_school": [
                "CBSE Fine Arts"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Hindi", "Sanskrit", "French"
            ],
            "college": [
                "Intermediate Hindi"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "CBSE Physical Education"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "ICSE": {
        "Math": {
            "high_school": [
                "ICSE Mathematics"
            ],
            "college": [
                "Calculus I"
            ]
        },
        "Science": {
            "high_school": [
                "ICSE Physics", "ICSE Chemistry", "ICSE Biology", "ICSE Science"
            ],
            "college": [
                "General Biology I", "General Chemistry I"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "ICSE English"
            ],
            "college": [
                "College Composition"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "ICSE History & Civics", "ICSE Geography"
            ],
            "college": [
                "World History (College)"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "ICSE Computer Studies"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "ICSE Commercial Studies"
            ],
            "college": [
                "Financial Accounting"
            ]
        },
        "Arts": {
            "high_school": [
                "ICSE Art"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Hindi", "Bengali", "French"
            ],
            "college": [
                "Intermediate Hindi"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "ICSE Physical Education"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "BANGLADESH": {
        "Math": {
            "high_school": [
                "General Mathematics (SSC)",
                "Higher Mathematics (SSC)",
                "Higher Mathematics (HSC)"
                ],
            "college": ["University Calculus I"]
        },
        "Science": {
            "high_school": [
                "Physics (SSC)",
                "Chemistry (SSC)",
                "Biology (SSC)",
                "Physics (HSC)",
                "Chemistry (HSC)",
                "Biology (HSC)"
                ],
            "college": ["General Biology I"]
        },
        "English / Language Arts": {
            "high_school": [
                "English 1st Paper (SSC)",
                "English 2nd Paper (SSC)",
                "English 1st Paper (HSC)",
                "English 2nd Paper (HSC)"
                ],
            "college": ["College Composition"]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "Bangladesh and Global Studies (SSC)",
                "Civics (HSC)",
                "Economics (HSC)",
                "Logic (HSC)",
                "History of Bangladesh & World Civilization (SSC)"
                ],
            "college": ["Economics"]
        },
        "Computer Science / Technology": {
            "high_school": [
                "ICT (SSC)",
                "ICT (HSC)"
                ],
            "college": ["Introduction to Computer Science"]
        }, 
        "Business / Commerce": {
            "high_school": [
                "Accounting (SSC)",
                "Business Studies (SSC)",
                "Finance & Banking (SSC)",
                "Accounting (HSC)",
                "Business Studies (HSC)",
                "Finance & Banking (HSC)"
                ],
            "college": ["Financial Accounting"]
        },
        "Arts": {
            "high_school": [
                "Fine Arts (SSC)",
                "Fine Arts (HSC)"
                ],
            "college": ["Art History"]
        },
        "Foreign Language": {
            "high_school": [
                "Bangla 1st Paper (SSC)",
                "Bangla 2nd Paper (SSC)",
                "Bangla 1st Paper (HSC)",
                "Bangla 2nd Paper (HSC)"
                ],
            "college": ["Bangla Literature"]
        },
        "Physical Education / Health": {
            "high_school": [
                "Physical Education (SSC)",
                "Physical Education (HSC)"
                ],
            "college": ["Sports Science"]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
        },


    "CANADA": {
        "Math": {
            "high_school": [
                "Grade 9 Math", "Grade 10 Math",
                "Functions", "Advanced Functions",
                "Calculus & Vectors"
            ],
            "college": [
                "Calculus I", "Linear Algebra"
            ]
        },
        "Science": {
            "high_school": [
                "Grade 9 Science", "Grade 10 Science",
                "Biology 11", "Biology 12",
                "Chemistry 11", "Chemistry 12",
                "Physics 11", "Physics 12"
            ],
            "college": [
                "General Biology I", "General Chemistry I", "Physics I (Mechanics)"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "English 9", "English 10", "English 11", "English 12"
            ],
            "college": [
                "College Composition"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "Canadian History", "World History", "Civics"
            ],
            "college": [
                "World History (College)"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "Computer Science 11", "Computer Science 12"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "Accounting 11", "Accounting 12", "Business Studies"
            ],
            "college": [
                "Financial Accounting"
            ]
        },
        "Arts": {
            "high_school": [
                "Visual Arts 11", "Visual Arts 12"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Core French", "Extended French"
            ],
            "college": [
                "Intermediate French"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "Physical Education"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "AUSTRALIA": {
        "Math": {
            "high_school": [
                "Mathematics Standard", "Mathematics Advanced",
                "Mathematics Extension 1", "Mathematics Extension 2"
            ],
            "college": [
                "Calculus I", "Linear Algebra"
            ]
        },
        "Science": {
            "high_school": [
                "Biology", "Chemistry", "Physics", "Earth & Environmental Science"
            ],
            "college": [
                "General Biology I", "General Chemistry I", "Physics I (Mechanics)"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "English Standard", "English Advanced", "English Extension"
            ],
            "college": [
                "College Composition"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "Modern History", "Ancient History", "Economics"
            ],
            "college": [
                "World History (College)", "Economics"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "Information Processes and Technology", "Software Design and Development"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "Business Studies", "Accounting"
            ],
            "college": [
                "Financial Accounting"
            ]
        },
        "Arts": {
            "high_school": [
                "Visual Arts", "Music", "Drama"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Japanese", "French", "Chinese"
            ],
            "college": [
                "Intermediate Japanese"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "Personal Development, Health and Physical Education (PDHPE)"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    },

    "OTHER": {
        "Math": {
            "high_school": [
                "General Math", "Mathematics", "Algebra I", "Geometry", "Algebra II",
                "Trigonometry", "Pre-Calculus", "Calculus"
            ],
            "college": [
                "College Algebra", "Calculus I", "Linear Algebra"
            ]
        },
        "Science": {
            "high_school": [
                "General Science", "Biology", "Chemistry", "Physics",
                "Environmental Science"
            ],
            "college": [
                "General Biology I", "General Chemistry I", "Physics I (Mechanics)"
            ]
        },
        "English / Language Arts": {
            "high_school": [
                "English", "English Literature"
            ],
            "college": [
                "College Composition"
            ]
        },
        "Social Studies / Humanities": {
            "high_school": [
                "History", "Geography", "Civics", "Economics"
            ],
            "college": [
                "World History (College)", "Economics"
            ]
        },
        "Computer Science / Technology": {
            "high_school": [
                "Computer Science", "Information Technology"
            ],
            "college": [
                "Introduction to Computer Science"
            ]
        },
        "Business / Commerce": {
            "high_school": [
                "Business Studies", "Accounting"
            ],
            "college": [
                "Financial Accounting"
            ]
        },
        "Arts": {
            "high_school": [
                "Visual Arts", "Music", "Drama"
            ],
            "college": [
                "Art History"
            ]
        },
        "Foreign Language": {
            "high_school": [
                "Foreign Language"
            ],
            "college": [
                "Intermediate Language Studies"
            ]
        },
        "Physical Education / Health": {
            "high_school": [
                "Physical Education", "Health"
            ],
            "college": [
                "Sports Science"
            ]
        },
        "Other": {
            "high_school": ["Other"],
            "college": ["Interdisciplinary Studies"]
        }
    }
}



COURSE_SIMILARITY = {
    "Biology": ["Honors Biology", "AP Biology", "IB Biology HL"],
    "Chemistry": ["Honors Chemistry", "AP Chemistry", "IB Chemistry HL"],
    "Physics": ["Honors Physics", "AP Physics 1", "AP Physics C: Mechanics"],
    "Algebra II": ["Pre-Calculus", "Trigonometry"],
    "Pre-Calculus": ["AP Calculus AB", "AP Statistics"],
    "IB Math AA SL": ["IB Math AA HL"],
    "General Mathematics": ["Higher Mathematics", "HSC Higher Math"],
    "CBSE Mathematics": ["Applied Mathematics", "Additional Mathematics"],
}

MATH_ORDER = {}

COURSE_PROGRESSION = {
    "USA": {
        "Math": {
            "General Math": ["Algebra I"],
            "Mathematics": ["Algebra I"],
            "Integrated Math I": ["Integrated Math II"],
            "Integrated Math II": ["Integrated Math III"],
            "Integrated Math III": ["Pre-Calculus"],
            "Algebra I": ["Geometry", "Algebra II"],
            "Geometry": ["Algebra II"],
            "Algebra II": ["Trigonometry", "Pre-Calculus"],
            "Trigonometry": ["Pre-Calculus"],
            "Pre-Calculus": ["AP Calculus AB"],
            "Honors Pre-Calculus": ["AP Calculus AB", "AP Calculus BC"],
            "AP Calculus AB": ["AP Calculus BC"],
            "AP Calculus BC": ["Multivariable Calculus"],
            "AP Statistics": ["College Statistics"],
            "College Algebra": ["Pre-Calculus"],
            "Multivariable Calculus": [],
            "Linear Algebra": [],
            "Differential Equations": [],
            "Discrete Mathematics": []
        },
        "Science": {
            "Biology": ["Honors Biology", "Chemistry"],
            "Honors Biology": ["AP Biology", "Chemistry"],
            "AP Biology": ["College Biology"],
            "Chemistry": ["Honors Chemistry", "Physics"],
            "Honors Chemistry": ["AP Chemistry", "Physics"],
            "AP Chemistry": ["College Chemistry"],
            "Physics": ["Honors Physics", "AP Physics 1"],
            "Honors Physics": ["AP Physics 1", "AP Physics C: Mechanics"],
            "AP Physics 1": ["AP Physics 2"],
            "AP Physics 2": ["AP Physics C: Mechanics"],
            "AP Physics C: Mechanics": ["AP Physics C: Electricity & Magnetism"],
            "AP Physics C: Electricity & Magnetism": [],
            "Environmental Science": ["AP Environmental Science"],
            "AP Environmental Science": []
        },
        "English / Language Arts": {
            "English 9": ["English 10"],
            "English 10": ["English 11"],
            "English 11": ["English 12"],
            "English 12": ["AP English Language", "AP English Literature"],
            "AP English Language": [],
            "AP English Literature": []
        },
        "Social Studies / Humanities": {
            "World History": ["US History"],
            "US History": ["Government", "Economics"],
            "Government": [],
            "Economics": []
        },
        "Computer Science / Technology": {
            "Computer Science": ["AP Computer Science Principles"],
            "AP Computer Science Principles": ["AP Computer Science A"],
            "AP Computer Science A": []
        },
        "Business / Commerce": {
            "Business Studies": ["Accounting", "Finance"],
            "Accounting": ["Finance"],
            "Finance": []
        },
        "Arts": {
            "Visual Arts": ["AP Art & Design"],
            "Fine Arts": ["AP Art & Design"],
            "AP Art & Design": []
        },
        "Foreign Language": {
            "Spanish": ["AP Spanish"],
            "French": ["AP French"],
            "German": [],
            "Mandarin": [],
            "Arabic": [],
            "AP Spanish": [],
            "AP French": []
        },
        "Physical Education / Health": {
            "Physical Education": [],
            "Health": []
        }
    },

    "IB": {
        "Math": {
            # MYP
            "MYP Mathematics": ["MYP Extended Mathematics", "IB Math AA SL", "IB Math AI SL"],
            "MYP Extended Mathematics": ["IB Math AA SL", "IB Math AI SL"],

            # SL
            "IB Math AA SL": ["IB Math AA HL"],
            "IB Math AI SL": ["IB Math AI HL"],

            # HL
            "IB Math AA HL": [
                "University Calculus",
                "University Linear Algebra",
                "University Statistics"
            ],
            "IB Math AI HL": [
                "University Statistics",
                "University Calculus"
            ],

            # University
            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "IB Biology SL": ["IB Biology HL"],
            "IB Biology HL": ["College Biology"],
            "IB Chemistry SL": ["IB Chemistry HL"],
            "IB Chemistry HL": ["College Chemistry"],
            "IB Physics SL": ["IB Physics HL"],
            "IB Physics HL": ["College Physics"],
            "IB Environmental Systems and Societies": []
        },
        "English / Language Arts": {
            "IB English A: Language & Literature SL": ["IB English A: Language & Literature HL"],
            "IB English A: Language & Literature HL": [],
            "IB English A: Literature SL": ["IB English A: Literature HL"],
            "IB English A: Literature HL": []
        },
        "Social Studies / Humanities": {
            "IB History SL": ["IB History HL"],
            "IB History HL": [],
            "IB Economics SL": ["IB Economics HL"],
            "IB Economics HL": [],
            "IB Psychology SL": ["IB Psychology HL"],
            "IB Psychology HL": []
        },
        "Computer Science / Technology": {
            "IB Computer Science SL": ["IB Computer Science HL"],
            "IB Computer Science HL": []
        },
        "Business / Commerce": {
            "IB Business Management SL": ["IB Business Management HL"],
            "IB Business Management HL": []
        },
        "Arts": {
            "IB Visual Arts SL": ["IB Visual Arts HL"],
            "IB Visual Arts HL": [],
            "IB Music SL": ["IB Music HL"],
            "IB Music HL": [],
            "IB Theatre SL": ["IB Theatre HL"],
            "IB Theatre HL": []
        },
        "Foreign Language": {
            "IB Language B SL": ["IB Language B HL"],
            "IB Language B HL": []
        },
        "Physical Education / Health": {
            "IB Sports, Exercise & Health Science": []
        }
    },

    "UK": {
        "Math": {
            "GCSE Mathematics": ["GCSE Further Mathematics", "AS Mathematics"],
            "GCSE Further Mathematics": ["AS Mathematics", "AS Further Mathematics"],

            "AS Mathematics": ["A-Level Mathematics"],
            "AS Further Mathematics": ["A-Level Further Mathematics"],

            "A-Level Mathematics": ["A-Level Further Mathematics", "University Calculus"],
            "A-Level Further Mathematics": [
            "University Calculus",
            "University Linear Algebra",
            "University Statistics"],

            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "GCSE Biology": ["A-Level Biology"],
            "A-Level Biology": ["University Biology"],
            "GCSE Chemistry": ["A-Level Chemistry"],
            "A-Level Chemistry": ["University Chemistry"],
            "GCSE Physics": ["A-Level Physics"],
            "A-Level Physics": ["University Physics"]
        },
        "English / Language Arts": {
            "GCSE English Language": ["A-Level English Language"],
            "A-Level English Language": [],
            "GCSE English Literature": ["A-Level English Literature"],
            "A-Level English Literature": []
        },
        "Social Studies / Humanities": {
            "GCSE History": ["A-Level History"],
            "A-Level History": [],
            "GCSE Geography": ["A-Level Geography"],
            "A-Level Geography": [],
            "A-Level Economics": []
        },
        "Computer Science / Technology": {
            "GCSE Computer Science": ["A-Level Computer Science"],
            "A-Level Computer Science": []
        },
        "Business / Commerce": {
            "GCSE Business Studies": ["A-Level Business Studies"],
            "A-Level Business Studies": [],
            "A-Level Accounting": [],
            "A-Level Economics": []
        },
        "Arts": {
            "GCSE Art & Design": ["A-Level Art & Design"],
            "A-Level Art & Design": []
        },
        "Foreign Language": {
            "GCSE French": ["A-Level French"],
            "A-Level French": [],
            "GCSE Spanish": ["A-Level Spanish"],
            "A-Level Spanish": [],
            "GCSE German": ["A-Level German"],
            "A-Level German": []
        },
        "Physical Education / Health": {
            "GCSE Physical Education": ["A-Level Physical Education"],
            "A-Level Physical Education": []
        }
    },

    "CAMBRIDGE": {
        "Math": {
            # IGCSE
            "IGCSE Mathematics": ["IGCSE Additional Mathematics", "AS Mathematics"],
            "IGCSE Additional Mathematics": ["AS Mathematics", "AS Further Mathematics"],

            # AS Level
            "AS Mathematics": ["A-Level Mathematics"],
            "AS Further Mathematics": ["A-Level Further Mathematics"],

            # A-Level
            "A-Level Mathematics": [
                "A-Level Further Mathematics",
                "University Calculus"
            ],
            "A-Level Further Mathematics": [
                "University Calculus",
                "University Linear Algebra",
                "University Statistics"
            ],

            # University
            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "Cambridge IGCSE Biology": ["A-Level Biology"],
            "A-Level Biology": ["University Biology"],
            "Cambridge IGCSE Chemistry": ["A-Level Chemistry"],
            "A-Level Chemistry": ["University Chemistry"],
            "Cambridge IGCSE Physics": ["A-Level Physics"],
            "A-Level Physics": ["University Physics"]
        },
        "English / Language Arts": {
            "Cambridge IGCSE English": ["Cambridge IGCSE Literature"],
            "Cambridge IGCSE Literature": []
        },
        "Social Studies / Humanities": {
            "Cambridge IGCSE History": [],
            "Cambridge IGCSE Geography": []
        },
        "Computer Science / Technology": {
            "Cambridge IGCSE Computer Science": []
        },
        "Business / Commerce": {
            "Cambridge IGCSE Business Studies": [],
            "Cambridge IGCSE Accounting": []
        },
        "Arts": {
            "Cambridge IGCSE Art & Design": []
        },
        "Foreign Language": {
            "Cambridge IGCSE Languages": []
        },
        "Physical Education / Health": {
            "Cambridge IGCSE Physical Education": []
        }
    },

    "CBSE": {
        "Math": {
            # Secondary
            "CBSE Mathematics (Basic)": ["CBSE Mathematics (Standard)"],
            "CBSE Mathematics (Standard)": ["CBSE Mathematics (Core)", "CBSE Applied Mathematics"],

            # Senior Secondary
            "CBSE Mathematics (Core)": [
                "CBSE Applied Mathematics",
                "University Calculus"
            ],
            "CBSE Applied Mathematics": [
                "University Calculus",
                "University Statistics",
                "University Linear Algebra"
            ],

            # University
            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "CBSE Physics": ["CBSE Chemistry"],
            "CBSE Chemistry": ["CBSE Biology"],
            "CBSE Biology": ["University Biology"],
            "CBSE Science": ["CBSE Physics"]
        },
        "English / Language Arts": {
            "CBSE English": []
        },
        "Social Studies / Humanities": {
            "CBSE Social Science": []
        },
        "Computer Science / Technology": {
            "CBSE Computer Applications": ["CBSE Informatics Practices"],
            "CBSE Informatics Practices": []
        },
        "Business / Commerce": {
            "CBSE Business Studies": ["CBSE Accountancy"],
            "CBSE Accountancy": ["CBSE Economics"],
            "CBSE Economics": []
        },
        "Arts": {
            "CBSE Fine Arts": []
        },
        "Foreign Language": {
            "Hindi": [],
            "Sanskrit": [],
            "French": []
        },
        "Physical Education / Health": {
            "CBSE Physical Education": []
        }
    },

    "ICSE": {
        "Math": {
            # ICSE
            "ICSE Mathematics": ["ICSE Commercial Mathematics", "ISC Mathematics"],
            "ICSE Commercial Mathematics": ["ISC Mathematics", "ISC Applied Mathematics"],

            # ISC
            "ISC Mathematics": [
                "ISC Applied Mathematics",
                "University Calculus"
            ],
            "ISC Applied Mathematics": [
                "University Calculus",
                "University Statistics",
                "University Linear Algebra"
            ],

            # University
            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "ICSE Physics": ["ICSE Chemistry"],
            "ICSE Chemistry": ["ICSE Biology"],
            "ICSE Biology": ["University Biology"],
            "ICSE Science": ["ICSE Physics"]
        },
        "English / Language Arts": {
            "ICSE English": []
        },
        "Social Studies / Humanities": {
            "ICSE History & Civics": [],
            "ICSE Geography": []
        },
        "Computer Science / Technology": {
            "ICSE Computer Studies": []
        },
        "Business / Commerce": {
            "ICSE Commercial Studies": []
        },
        "Arts": {
            "ICSE Art": []
        },
        "Foreign Language": {
            "Hindi": [],
            "Bengali": [],
            "French": []
        },
        "Physical Education / Health": {
            "ICSE Physical Education": []
        }
    },

    "BANGLADESH": {
        "Math": {
            # SSC
            "General Mathematics (SSC)": ["Higher Mathematics (SSC)"],
            "Higher Mathematics (SSC)": ["Higher Mathematics (HSC)"],

            # HSC
            "Higher Mathematics (HSC)": [
                "University Calculus I",
                "University Statistics"
            ],

            # University
            "University Calculus I": ["University Calculus II", "University Linear Algebra"],
            "University Calculus II": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "Physics (SSC)": ["Physics (HSC)"],
            "Chemistry (SSC)": ["Chemistry (HSC)"],
            "Biology (SSC)": ["Biology (HSC)"],
            "Physics (HSC)": ["University Physics"],
            "Chemistry (HSC)": ["University Chemistry"],
            "Biology (HSC)": ["University Biology"]
        },
        "English / Language Arts": {
            "English 1st Paper (SSC)": ["English 2nd Paper (SSC)"],
            "English 2nd Paper (SSC)": ["English 1st Paper (HSC)"],
            "English 1st Paper (HSC)": ["English 2nd Paper (HSC)"],
            "English 2nd Paper (HSC)": []
        },
        "Social Studies / Humanities": {
            "Bangladesh and Global Studies (SSC)": ["Civics (HSC)"],
            "Civics (HSC)": ["Economics (HSC)"],
            "Economics (HSC)": [],
            "Logic (HSC)": [],
            "History of Bangladesh & World Civilization (SSC)": []
        },
        "Computer Science / Technology": {
            "ICT (SSC)": ["ICT (HSC)"],
            "ICT (HSC)": []
        },
        "Business / Commerce": {
            "Accounting (SSC)": ["Accounting (HSC)"],
            "Business Studies (SSC)": ["Business Studies (HSC)"],
            "Finance & Banking (SSC)": ["Finance & Banking (HSC)"],
            "Accounting (HSC)": [],
            "Business Studies (HSC)": [],
            "Finance & Banking (HSC)": []
        },
        "Arts": {
            "Fine Arts (SSC)": ["Fine Arts (HSC)"],
            "Fine Arts (HSC)": []
        },
        "Foreign Language": {
            "Bangla 1st Paper (SSC)": ["Bangla 2nd Paper (SSC)"],
            "Bangla 2nd Paper (SSC)": ["Bangla 1st Paper (HSC)"],
            "Bangla 1st Paper (HSC)": ["Bangla 2nd Paper (HSC)"],
            "Bangla 2nd Paper (HSC)": []
        },
        "Physical Education / Health": {
            "Physical Education (SSC)": ["Physical Education (HSC)"],
            "Physical Education (HSC)": []
        }
    },

    "CANADA": {
        "Math": {
            # Grade 9
            "MTH1W": ["MPM2D", "MFM2P"],

            # Grade 10
            "MPM2D": ["MCR3U", "MCF3M"],
            "MFM2P": ["MCF3M", "MBF3C"],

            # Grade 11
            "MCR3U": ["MHF4U", "MCV4U"],
            "MCF3M": ["MHF4U", "MDM4U"],
            "MBF3C": ["MAP4C"],

            # Grade 12
            "MHF4U": ["MCV4U", "University Calculus"],
            "MCV4U": [
                "University Calculus",
                "University Linear Algebra",
                "University Statistics"
            ],
            "MDM4U": ["University Statistics"],
            "MAP4C": [],

            # University
            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "Grade 9 Science": ["Grade 10 Science"],
            "Grade 10 Science": ["Biology 11", "Chemistry 11", "Physics 11"],
            "Biology 11": ["Biology 12"],
            "Biology 12": ["University Biology"],
            "Chemistry 11": ["Chemistry 12"],
            "Chemistry 12": ["University Chemistry"],
            "Physics 11": ["Physics 12"],
            "Physics 12": ["University Physics"]
        },
        "English / Language Arts": {
            "English 9": ["English 10"],
            "English 10": ["English 11"],
            "English 11": ["English 12"],
            "English 12": []
        },
        "Social Studies / Humanities": {
            "Canadian History": ["World History"],
            "World History": ["Civics"],
            "Civics": []
        },
        "Computer Science / Technology": {
            "Computer Science 11": ["Computer Science 12"],
            "Computer Science 12": []
        },
        "Business / Commerce": {
            "Accounting 11": ["Accounting 12"],
            "Accounting 12": [],
            "Business Studies": []
        },
        "Arts": {
            "Visual Arts 11": ["Visual Arts 12"],
            "Visual Arts 12": []
        },
        "Foreign Language": {
            "Core French": ["Extended French"],
            "Extended French": []
        },
        "Physical Education / Health": {
            "Physical Education": []
        }
    },

    "AUSTRALIA": {
        "Math": {
            # Years 7–10
            "Mathematics (Year 7)": ["Mathematics (Year 8)"],
            "Mathematics (Year 8)": ["Mathematics (Year 9)"],
            "Mathematics (Year 9)": ["Mathematics (Year 10)"],
            "Mathematics (Year 10)": [
                "Essential Mathematics",
                "General Mathematics",
                "Mathematical Methods"
            ],

            # ATAR Senior Secondary
            "Essential Mathematics": [],
            "General Mathematics": ["Mathematical Methods"],
            "Mathematical Methods": [
                "Specialist Mathematics",
                "University Calculus"
            ],
            "Specialist Mathematics": [
                "University Calculus",
                "University Linear Algebra",
                "University Statistics"
            ],

            # University
            "University Calculus": ["University Linear Algebra", "University Statistics"],
            "University Linear Algebra": ["University Statistics"],
            "University Statistics": []
        },
        "Science": {
            "Biology": ["University Biology"],
            "Chemistry": ["University Chemistry"],
            "Physics": ["University Physics"],
            "Earth & Environmental Science": []
        },
        "English / Language Arts": {
            "English": []
        },
        "Social Studies / Humanities": {
            "History": [],
            "Geography": []
        },
        "Computer Science / Technology": {
            "Computer Science": []
        },
        "Business / Commerce": {
            "Business Studies": []
        },
        "Arts": {
            "Visual Arts": []
        },
        "Foreign Language": {
            "Languages": []
        },
        "Physical Education / Health": {
            "Physical Education": []
        }
    }
}




MATH_ORDER["USA"] = [
    "General Math",
    "Mathematics",
    "Integrated Math",
    "Integrated Math I",
    "Integrated Math II",
    "Integrated Math III",
    "Algebra I",
    "Geometry",
    "Algebra II",
    "Trigonometry",
    "Pre-Calculus",
    "Honors Pre-Calculus",
    "Functions & Relations",
    "AP Calculus AB",
    "AP Calculus BC",
    "AP Statistics"
]

MATH_ORDER["IB"] = [
    # MYP
    "MYP Mathematics",
    "MYP Extended Mathematics",

    # DP SL
    "IB Math AA SL",
    "IB Math AI SL",

    # DP HL
    "IB Math AA HL",
    "IB Math AI HL",

    # University Prep
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["UK"] = [
    # GCSE Level
    "GCSE Mathematics",
    "GCSE Further Mathematics",

    # AS Level
    "AS Mathematics",
    "AS Further Mathematics",

    # A-Level
    "A-Level Mathematics",
    "A-Level Further Mathematics",

    # University Prep / Advanced
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["Cambridge"] = [
    # IGCSE
    "IGCSE Mathematics",
    "IGCSE Additional Mathematics",

    # AS Level
    "AS Mathematics",
    "AS Further Mathematics",

    # A-Level
    "A-Level Mathematics",
    "A-Level Further Mathematics",

    # University Prep
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["CBSE"] = [
    # Secondary (9–10)
    "CBSE Mathematics (Basic)",
    "CBSE Mathematics (Standard)",

    # Senior Secondary (11–12)
    "CBSE Mathematics (Core)",
    "CBSE Applied Mathematics",

    # University Prep
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["ICSE"] = [
    # ICSE (Class 9–10)
    "ICSE Mathematics",
    "ICSE Commercial Mathematics",

    # ISC (Class 11–12)
    "ISC Mathematics",
    "ISC Applied Mathematics",

    # University Prep
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["Bangladesh"] = [
    # SSC
    "General Mathematics (SSC)",
    "Higher Mathematics (SSC)",

    # HSC
    "Higher Mathematics (HSC)",

    # University Prep
    "University Calculus I",
    "University Calculus II",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["Canada"] = [
    # Grade 9
    "MTH1W",

    # Grade 10
    "MPM2D",
    "MFM2P",

    # Grade 11
    "MCR3U",
    "MCF3M",
    "MBF3C",

    # Grade 12
    "MHF4U",
    "MCV4U",
    "MDM4U",
    "MAP4C",

    # University Prep
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

MATH_ORDER["Australia"] = [
    # Years 7–10
    "Mathematics (Year 7)",
    "Mathematics (Year 8)",
    "Mathematics (Year 9)",
    "Mathematics (Year 10)",

    # ATAR Senior Secondary
    "Essential Mathematics",
    "General Mathematics",
    "Mathematical Methods",
    "Specialist Mathematics",

    # University Prep
    "University Calculus",
    "University Linear Algebra",
    "University Statistics"
]

SCIENCE_ORDER = {
    "General Science": [
        "General Science", "Integrated Science", "Physical Science", "Life Science"
    ],

    "Biology": [
        "Biology", "Honors Biology", "AP Biology"
    ],

    "Chemistry": [
        "Chemistry", "Honors Chemistry", "AP Chemistry"
    ],

    "Physics": [
        "Physics", "Honors Physics",
        "AP Physics 1", "AP Physics 2",
        "AP Physics C: Mechanics",
        "AP Physics C: Electricity & Magnetism"
    ],

    "Environmental Science": [
        "Environmental Science", "AP Environmental Science"
    ],

    "Earth Science": [
        "Earth Science"
    ],

    "Marine Science": [
        "Marine Science"
    ]
}





#helper to remove lower level courses

def _remove_lower_level_math(courses, taken, curriculum):
    # Get the ordering list for this curriculum
    order = MATH_ORDER.get(curriculum, [])

    # Find highest-level taken math course
    highest_index = -1
    for t in taken:
        if t in order:
            idx = order.index(t)
            highest_index = max(highest_index, idx)


    # If no taken math matches the order list, return original
    if highest_index == -1:
        return courses

    # Allowed = all courses at or ABOVE the highest taken
    allowed = set(order[highest_index:])

    filtered = [c for c in courses if c in allowed]

    return filtered


#----------------------------------------------------------------------

def get_next_courses(curriculum, category, completed_courses):
    """
    Returns the next recommended courses based on progression rules.
    """
    if curriculum not in COURSE_PROGRESSION:
        return []

    if category not in COURSE_PROGRESSION[curriculum]:
        return []

    progression_map = COURSE_PROGRESSION[curriculum][category]

    # Find the highest-level completed course
    highest = None
    for course in completed_courses:
        if course in progression_map:
            highest = course

    if not highest:
        return []

    # Get next courses from progression
    next_list = progression_map.get(highest, [])

    # Remove courses already taken
    next_list = [c for c in next_list if c not in completed_courses]

    return next_list




# ============================================================
#  CATEGORY SCORING
# ============================================================

def compute_category_scores(transcript, letter_scale):

    letter_points = {item["Letter"]: item["Points"] for item in letter_scale}
    category_scores = defaultdict(float)

    for grade in transcript.get("Grades", []):
        for sub in grade.get("Subjects", []):
            cat = sub.get("MainCategory")
            if not cat:
                continue

            marks = sub.get("Marks") or 0
            letter = sub.get("Letter")
            pref = sub.get("Preference") or 0
            credits = sub.get("Credits") or 0

            points = letter_points.get(letter, 0)

            score = (marks * 0.5) + (points * 10) + (pref * 5) + (credits * 2)
            category_scores[cat] += score

    return dict(category_scores)

# ============================================================
#  HELPERS
# ============================================================

def _get_progression_next(curriculum, category, course):
    """
    Returns the next courses for a given course using the new progression map.
    """
    if curriculum not in COURSE_PROGRESSION:
        return []

    if category not in COURSE_PROGRESSION[curriculum]:
        return []

    prog_map = COURSE_PROGRESSION[curriculum][category]

    # prog_map is now: { "Algebra I": ["Geometry", "Algebra II"], ... }
    return prog_map.get(course, [])


def _augment_with_similarity_and_progression(transcript, curriculum, base_by_cat):
    taken = _get_taken_courses(transcript)
    augmented = {cat: list(courses) for cat, courses in base_by_cat.items()}

    for grade in transcript.get("Grades", []):
        for sub in grade.get("Subjects", []):
            raw_cat = sub.get("MainCategory")
            raw_name = sub.get("Name") or sub.get("CourseName") or sub.get("CustomCourseName")

            if not raw_cat or not raw_name:
                continue

            cat = raw_cat.strip()
            base_name = get_science_base_subject(raw_name.strip())

            augmented.setdefault(cat, [])

            # 1. PROGRESSION
            next_courses = _get_progression_next(curriculum, cat, base_name)
            for nxt in reversed(next_courses):
                if nxt not in taken and nxt not in augmented[cat]:
                    augmented[cat].append(nxt)

            # 2. SIMILARITY
            similar = COURSE_SIMILARITY.get(base_name, [])
            for c in reversed(similar):
                if c not in taken and c not in augmented[cat]:
                    augmented[cat].append(c)

    return augmented










def get_top_categories(category_scores, threshold=0.95):
    if not category_scores:
        return []

    sorted_scores = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    top_score = sorted_scores[0][1]

    # Hybrid: include all categories within 95% of top
    return [cat for cat, score in sorted_scores if score >= top_score * threshold]


def _get_taken_courses(transcript):
    taken = set()

    for grade in transcript.get("Grades", []):
        for sub in grade.get("Subjects", []):
            raw = sub.get("Name") or sub.get("CourseName") or sub.get("CustomCourseName")
            if not raw:
                continue

            base = get_science_base_subject(raw)
            taken.add(base)

    return taken




def _filter_and_rank_courses(base_list, taken_courses):
    # Preserve original order, only remove taken courses
    return [c for c in base_list if c not in taken_courses]



def _balanced_merge(category_to_courses, total_limit=10):
    """
    Correct merge:
    - Preserve the order inside each category list (progression stays first)
    - Merge categories in the order they appear
    - Stop at total_limit
    """
    result = []
    seen = set()

    # Iterate categories in the order they appear
    for cat, courses in category_to_courses.items():
        for c in courses:
            if c not in seen:
                seen.add(c)
                result.append(c)
            if len(result) >= total_limit:
                return result

    return result



# ============================================================
#  HYBRID RECOMMENDER (MULTI-CATEGORY + BALANCED)
# ============================================================

def recommend_courses_hybrid(transcript, category_scores, curriculum="USA"):

    if not category_scores:
        return [], [], []

    top_categories = get_top_categories(category_scores, threshold=0.95)
    taken = _get_taken_courses(transcript)

    catalog_for_curr = COURSE_CATALOG.get(curriculum, COURSE_CATALOG["OTHER"])

    hs_by_cat = {}
    college_by_cat = {}

    letter_scale = transcript.get("letterScale", [])

    for cat in top_categories:
        cat_catalog = catalog_for_curr.get(cat) or catalog_for_curr.get("Other") or {}
        hs_list = cat_catalog.get("high_school", [])
        college_list = cat_catalog.get("college", [])

        # ⭐ SCIENCE ENGINE
        if cat.lower() == "science":
            sub_scores = compute_subsubject_scores(transcript, letter_scale)
            ordered_subs = sort_subsubjects_by_strength(sub_scores)

            merged = []

            for sub in ordered_subs:
                if sub in SCIENCE_ORDER:
                    for course in SCIENCE_ORDER[sub]:
                        if course in hs_list and course not in merged:
                            merged.append(course)

            for c in hs_list:
                if c not in merged:
                    merged.append(c)

            hs_by_cat[cat] = [c for c in merged if c not in taken]
            college_by_cat[cat] = _filter_and_rank_courses(college_list, taken)
            continue

        # ⭐ OTHER CATEGORIES
        filtered = _filter_and_rank_courses(hs_list, taken)

        if cat == "Math":
            filtered = _remove_lower_level_math(filtered, taken, curriculum)

        hs_by_cat[cat] = filtered
        college_by_cat[cat] = _filter_and_rank_courses(college_list, taken)

    # ⭐ AUGMENTATION
    hs_by_cat = _augment_with_similarity_and_progression(transcript, curriculum, hs_by_cat)

    # ⭐ MERGE
    hs_recs = _balanced_merge(hs_by_cat, total_limit=10)
    college_recs = _balanced_merge(college_by_cat, total_limit=10)

    return top_categories, hs_recs, college_recs







# ============================================================
#  TRACK ENGINE
# ============================================================

def suggest_tracks(category_scores):
    if not category_scores:
        return []

    sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    top_cats = [c for c, _ in sorted_cats[:3]]

    tracks = []

    if "Math" in top_cats or "Science" in top_cats:
        tracks.append("STEM Track")
    if "Math" in top_cats and "Computer Science / Technology" in top_cats:
        tracks.append("Engineering Track")
        tracks.append("Computer Science Track")
    if "Science" in top_cats and "Physical Education / Health" in top_cats:
        tracks.append("Pre-Med / Health Sciences Track")
    if "Business / Commerce" in top_cats and "Math" in top_cats:
        tracks.append("Business / Finance Track")
        tracks.append("Data Science Track")
    if "English / Language Arts" in top_cats or "Social Studies / Humanities" in top_cats:
        tracks.append("Humanities Track")
        tracks.append("Communications / Media Track")
    if "Arts" in top_cats:
        tracks.append("Arts / Design Track")
    if "Foreign Language" in top_cats:
        tracks.append("International Studies Track")

    if not tracks:
        tracks.append("General Academic Track")

    seen = set()
    out = []
    for t in tracks:
        if t not in seen:
            seen.add(t)
            out.append(t)

    return out


#calculating sub subject scores for science subjects.------------------------

def _convert_grade_to_score(sub, letter_scale):
    """
    Convert a subject's grade into a normalized performance score [0,1]
    using the SAME logic as the frontend:
    - marks → letter (via user grading scale)
    - letter → points (via letterToPoint)
    """

    # 1. Extract marks (your system uses Marks or Percentage)
    marks = (
        sub.get("Marks") or
        sub.get("Percentage") or
        sub.get("Score") or
        None
    )

    # 2. Extract letter if already present
    letter = (
        sub.get("LetterGrade") or
        sub.get("Grade") or
        None
    )

    # --- CASE A: If marks exist, convert marks → letter using letter_scale ---
    if marks is not None and letter_scale:
        for rule in letter_scale:
            if marks >= rule.get("min", 0):
                letter = rule.get("letter")
                break

    # --- CASE B: If no letter found, fallback to neutral ---
    if not letter:
        return 0.6  # neutral fallback

    # --- Convert letter → points (your exact frontend mapping) ---
    letter_points_map = {
        "A+": 4, "A": 4, "A-": 3.7,
        "B+": 3.3, "B": 3, "B-": 2.7,
        "C+": 2.3, "C": 2,
        "D": 1, "F": 0
    }

    points = letter_points_map.get(letter.upper(), 0)

    # --- Normalize points to 0–1 scale ---
    score = points / 4.0

    return max(0.0, min(1.0, score))

def compute_subject_strength(sub, letter_scale):
    """
    Convert a subject entry into a normalized 0–1 strength score.
    Uses marks, letter grade, and preference.
    """

    # 1. Marks (0–100 → 0–1)
    marks = sub.get("Marks")
    marks_score = (marks / 100) if isinstance(marks, (int, float)) else 0

    # 2. Letter grade (A, B, C → numeric)
    letter = sub.get("Letter")
    letter_score = 0
    if letter and letter_scale:
        # letter_scale is like: [{"letter": "A", "value": 4.0}, ...]
        for item in letter_scale:
            if item.get("letter") == letter:
                # Normalize 0–4 scale → 0–1
                letter_score = item.get("value", 0) / 4.0
                break

    # 3. Preference (1–5 → 0–1)
    pref = sub.get("Preference")
    pref_score = (pref / 5) if isinstance(pref, (int, float)) else 0

    # Weighted average (you can adjust weights)
    return (marks_score * 0.5) + (letter_score * 0.3) + (pref_score * 0.2)



def compute_subsubject_scores(transcript, letter_scale):
    scores = {}

    for grade in transcript.get("Grades", []):
        for sub in grade.get("Subjects", []):
            raw = sub.get("Name") or sub.get("CourseName") or sub.get("CustomCourseName")
            if not raw:
                continue

            base = get_science_base_subject(raw)
            if not base:
                continue

            score = compute_subject_strength(sub, letter_scale)
            scores[base] = scores.get(base, 0) + score

    return scores



def sort_subsubjects_by_strength(sub_scores):
    return sorted(
        sub_scores.keys(),
        key=lambda s: (-sub_scores[s], s)  # tie-break alphabetically
    )




def get_science_base_subject(name):
    if not name:
        return None

    n = name.lower()

    if "biology" in n:
        return "Biology"
    if "chemistry" in n:
        return "Chemistry"
    if "physics" in n:
        return "Physics"
    if "environmental" in n:
        return "Environmental Science"
    if "earth" in n:
        return "Earth Science"
    if "marine" in n:
        return "Marine Science"
    if "integrated" in n or "general" in n or "physical science" in n or "life science" in n:
        return "General Science"

    return name.strip()




