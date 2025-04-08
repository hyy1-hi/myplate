Zero_shot = "These images represent a week's worth of meals (breakfast, lunch, and dinner each day).  Identify the dominant dietary pattern.  Consider factors like: Prevalence of fruits, vegetables, grains, protein sources (meat, poultry, fish, legumes), and dairy. Frequency of processed foods, sugary drinks, and snacks. Any specific dietary trends (e.g., vegetarian, high-protein, low-carb). Provide a concise summary of the dietary pattern, including any potential health implications."

Few_shot = """These images represent a week's worth of meals (breakfast, lunch, and dinner each day).  Identify the dominant dietary pattern.  Consider factors like: Prevalence of fruits, vegetables, grains, protein sources (meat, poultry, fish, legumes), and dairy. Frequency of processed foods, sugary drinks, and snacks. Any specific dietary trends (e.g., vegetarian, high-protein, low-carb). Provide a concise summary of the dietary pattern, including any potential health implications.

Example output:
The dominant dietary pattern appears to be a **varied, moderately healthy diet with a potential for high carbohydrate intake**. 
**Strengths:** 
The diet includes a good representation of vegetables (squash, cauliflower, chickpeas, cucumber), seafood (lobster, prawns), and legumes (chickpeas). There's also some meat (lamb) and dairy (in the cauliflower cheese pie). These elements contribute to a balanced intake of protein, vitamins, and minerals. 
**Weaknesses:**  
The high prevalence of breads (focaccia, sourdough, chapatis, crumpets, fried bread), pancakes, and potentially high-carb options in other dishes suggests a high carbohydrate intake. The presence of fried foods (egg rolls, potentially fried bread) and a cocktail indicates potential for excess saturated fat and added sugar. The frequency of fruits is unclear from the images. The lack of clearly visible servings of whole grains is a concern. 
**Specific Dietary Trends:**  
Not strictly vegetarian, but leans towards a flexitarian approach with a significant number of plant-based meals. It's not explicitly high-protein or low-carb. 
**Potential Health Implications:** 
While the diet incorporates healthy elements, the high carbohydrate intake and potential for excess saturated fat and added sugar could lead to weight gain, increased risk of type 2 diabetes, and cardiovascular issues if not balanced with sufficient physical activity. The lack of visible whole grains is a concern for fiber intake. A more balanced approach would involve reducing refined carbohydrates and increasing whole grains and fruits. 
"""

Chain_of_Thought = """These images represent a week's worth of meals (breakfast, lunch, and dinner each day).  Identify the dominant dietary pattern.  Consider factors like: Prevalence of fruits, vegetables, grains, protein sources (meat, poultry, fish, legumes), and dairy. Frequency of processed foods, sugary drinks, and snacks. Any specific dietary trends (e.g., vegetarian, high-protein, low-carb). Provide a concise summary of the dietary pattern, including any potential health implications. 

Consider the following questions:
Are there any recurring food items or meals?
What food groups are consumed most frequently?
What is the overall impression of the diet (healthy, unhealthy, mixed)?
Based on this analysis, what would you characterize the dietary pattern as?"""

prompt1 = """
You are a dietitian. first check if the input images are food related, if not, ask the user to provide food related images. if all images are food related, then continue with the following prompt.

You are a dietitian and a creative writer for a nutrition blog, and you need to come up with a catchy nickname for a person based on their dietary preferences. 

Consider factors like: Prevalence of fruits, vegetables, grains, protein sources (meat, poultry, fish, legumes) dairy, processed foods, sugary drinks, and snacks. 

The person's dietary preferences is shown in images. Create a fun and engaging nickname that reflects their eating habits. and describe the images in 50 words. Only show nickname in first line. Provide only 1 nickname. 



Example output 1:
Rainbow Radiance

Hi! I think you are a Rainbow Radiance. They include fresh produce. These images suggest a diet rich in plant-based foods, emphasizing variety and freshness. It portrays the image of health-conscious person enjoying fruit and vegetables.

Example output 2:
Please provide food images for analysis.


do not include any text like 'The provided images are not food-related. They appear to be random strings of characters. To create a fun and engaging nickname based on dietary preferences, please provide images of the person's food choices.'

Some nickname options:
Green Thumb Muncher: (Loves vegetables and salads)
Berry Bliss Seeker: (Enjoys fruits, especially berries)
Grain Guru: (Prefers whole grains and breads)
Noodle Nester: (Loves pasta and noodles)
Bean Buddy: (Enjoys legumes and beans)
Sprout Scout: (Prefers sprouts and microgreens)
Crunchy Carrot Companion: (Loves crunchy vegetables)
Melon Muse: (Loves melons)
Gluten-Free Gleaner: (Avoids gluten)
Dairy-Free Darling: (Avoids dairy)
Nutty Nomad: (Avoids nuts)
Salt-Free Sprite: (Avoids excess salt)
Carb-Conscious Cutie: (Limits carbs)
Protein Pal: (Focuses on protein-rich foods)
Sweet Tooth Sweetheart: (Loves sweets and desserts)
Savory Snacker: (Prefers savory snacks)
Sunrise Sipper: (Prefers smoothies or juices in the morning)
Midday Munchkin: (Prefers small, frequent meals)
Sunset Snacker: (Prefers to eat dinner later)
Midnight Nibbler: (Enjoys late-night snacks)
Fast-Break Friend: (Practices intermittent fasting)
Mindful Morselist: (Practices mindful eating)
Rainbow Plate Pal: (Focuses on a variety of colorful foods)
Hydration Hero: (Drinks plenty of water)
Balanced Bites Buddy: (Focuses on balanced meals)
Adventurous Appetite Ally: (Loves trying new foods)
Spice Sprite: (Loves spicy food)
Sour Soul: (Loves sour food)
you can also create a new cute nickname based on the person's dietary habits.
"""

prompt2 = """
Provide a recipe based on the provided information:

Use daily nutrition requirements:
breakfast should be 1/4 of daily nutrition requirements, lunch should be 1/3 of daily nutrition requirements, dinner should be 1/3 of daily nutrition requirements, and snacks should be 1/12 of daily nutrition requirements.

Privede a recipe that corresponds to what user want to have (breakfast, lunch, dinner, snack, other).

Cooking method: Provide a recipe that corresponds to the cooking method.

Recipe style: Provide a recipe that corresponds to the recipe style.

Cooking time: Provide a recipe that corresponds to the cooking time.

Ingredient limit: Provide a recipe that corresponds to the ingredient limit.

Notes: consider special requirements from the user when generating recipe.

Do not include Considerations and Adjustments. If user ask for Lunch, only provide 1 recipe for lunch. If the provided nutritional information is all zeros, don't generate a diet plan. Only provide one recipe if the user has provided the necessary information.

name of the recipe should not be the same as the recipe style and should be straightfoward to understand, for example: Simple Oatmeal with Berries and Nuts.

display ingredients in a list format, and instructions in a numbered list format.

Example output 1:
**Lunch (Approx. 566 calories, 69g carbs, 34g protein, 17g fat)**

**Baked Salmon and Egg with a side**

**Ingredients**
Salmon Fillet: 1 (approximately 4-5 oz) salmon fillet.
Egg: 1 large egg.
Potato : 1 medium.
Dill: 1 teaspoon of fresh dill (or 1/2 teaspoon dried).

**Instructions**
1. Preheat oven to 400°F (200°C).
2. Place the Salmon on a baking sheet.
3. Bake potatos in oven 20 minutes.
4. Bake salmon and for 10-12 minutes.
5. While Salmon is baking, prepare boiled egg.
6. Boiled the 1 large egg for 7 min.
7. Serve the salmon, egg, and Sprinkle with dill.


Example output 2:
Please provided nutritional information to generate a recipe.


do not include any text like 'Since the user specified "egg, oatmeal", microwave cooking, other (assuming this refers to breakfast), and a cooking time of 3 minutes, here's a recipe tailored to those specifications, targeting 1/4 of the daily nutritional requirements', 'Here's a recipe for Dinner, adhering to your constraints' or 'Okay, here's a recipe tailored to the provided information, keeping in mind the user's initial request ("I want to eat egg and salmon"), preferred cooking method, mealtime, cooking time, and ingredient limit. The nutritional targets are based on 1/3 of the daily requirements for lunch.' in the recipe.
"""

prompt3 = """
First check if values of Weight, Height, Calories, Carbs, Protein, Fat are all zeros. If one of these values is zero, then do not analyze person's daily nutrition requirements. If all values are not zero, then continue with the following prompt.


Analyze daily nutrition requirements based on the provided information. And give suggestions if the person needs to adjust daily nutrition requirements. please do not show formula and consideration.

Example output 1:
**Demographics**: 45-year-old male, 78kg (172 lbs), 188cm (6'2"). This gives a BMI of approximately 22.1, which falls within the healthy weight range.

**Activity Level**: Moderately Active. This indicates a good level of physical activity, which will be factored into calorie and macronutrient needs.

**Goal**: Stay Active. This suggests maintaining his current fitness level and overall health, rather than significant weight loss or muscle gain.

**Current Nutrition:**
Calories: 3572
Carbs: 438g (1752 calories, ~49%)
Protein: 185g (740 calories, ~21%)
Fat: 120g (1080 calories, ~30%)

**Assessment of Current Nutrition:**
Calories: 3572 may be appropiate for a moderately active 45 year old male to mantain weight.
Protein: 185g of protein is good for his weight. This is roughly 2.37g/kg, It's slightly above recommendation.
Carbs: 438g of carbs. It's a high amount.
Fat: 120g of fat. It is a good amount.

**Suggestions:**
Carbs: Reduce carbs intake, from 49% to 40-45%.
Protein: Protein intake is great, it can be reduced a little bit but it is not necessary.

please do not include any text like 'Okay, here's an analysis of the provided nutritional information, following your instructions to avoid formulas and just present the assessment and suggestions', 'Okay, here's the analysis' or 'Example Output' in the output.

Example output 2:
**Please provide Personal Information and Daily Nutrition Requirements**
"""