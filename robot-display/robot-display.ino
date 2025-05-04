#include <TFT_eSPI.h>
#include <elapsedMillis.h>

TFT_eSPI tft = TFT_eSPI();   

enum Face {IDLE, LISTEN, SPEAK};

#define BG_COLOR TFT_BLACK
#define FG_COLOR TFT_GREEN

constexpr int DISPLAY_WIDTH=480;
constexpr int DISPLAY_HEIGHT=320;

constexpr int EYE_WIDTH=DISPLAY_WIDTH*0.2;
constexpr int EYE_HEIGHT=DISPLAY_HEIGHT*0.33;
constexpr int EYE_LEFT_POS_X=DISPLAY_WIDTH*0.30 - EYE_WIDTH*0.5;
constexpr int EYE_RIGHT_POS_X=DISPLAY_HEIGHT*0.70 + EYE_WIDTH*0.5;
constexpr int EYE_POS_Y = DISPLAY_HEIGHT*0.4 - EYE_HEIGHT*0.75;
constexpr int EYE_CORNER_RADIUS=4;
constexpr int EYE_ANIM_BLINK_TOTAL_TIME = 200;
constexpr int EYE_ANIM_BLINK_DRAW_TIME = 15;

// constexpr int MOUTH_POS_X = EYE_LEFT_POS_X;
constexpr int MOUTH_POS_X = EYE_LEFT_POS_X + 0.5*EYE_WIDTH;
constexpr int MOUTH_POS_Y = EYE_POS_Y + EYE_HEIGHT + 4;
// constexpr int MOUTH_WIDTH = EYE_RIGHT_POS_X + EYE_WIDTH - EYE_LEFT_POS_X;
constexpr int MOUTH_WIDTH = EYE_RIGHT_POS_X - EYE_LEFT_POS_X ;//+ 0.5*EYE_WIDTH;
constexpr int MOUTH_HEIGHT = DISPLAY_HEIGHT*0.4;
constexpr int MOUTH_ACTIVE_WIDTH=MOUTH_WIDTH*0.2;
constexpr int MOUTH_SMILE_START_X = MOUTH_POS_X*1.25;
constexpr int MOUTH_SMILE_END_X = MOUTH_POS_X + MOUTH_WIDTH/1.2;
constexpr int MOUTH_SMILE_DISPL_X = 18;
constexpr int MOUTH_SMILE_DISPL_Y = 15;
constexpr int MOUTH_SMILE_POS_Y =  MOUTH_POS_Y+0.65*MOUTH_HEIGHT;

constexpr int EAR_BIG_OUTER_RADIUS = EYE_HEIGHT*0.5;
constexpr int EAR_BIG_INNER_RADIUS = EYE_HEIGHT*0.5 - 5;
constexpr int EAR_BIG_START_ANGLE = 10;
constexpr int EAR_BIG_END_ANGLE = 170;
constexpr int EAR_SMALL_START_ANGLE = 165;
constexpr int EAR_SMALL_END_ANGLE = 15;
constexpr int EAR_SMALL_OUTER_RADIUS = EYE_HEIGHT*0.2;
constexpr int EAR_SMALL_INNER_RADIUS = EYE_HEIGHT*0.2 - 3;
constexpr int EAR_POS_Y = EYE_POS_Y + 10;

void drawSmile();
void drawFace(int offx=0, int offy=0);
void drawEyes(int offx=0,int offy=0);
void cleanEyes(int offx=0,int offy=0);
void drawEyesBorder(int offx=0,int offy=0);
void animationIdle();
void animationBlink(bool fullface=false);
void animationListen();
void animationSpeak();

Face face = IDLE;

void setup() {
  Serial.begin(115200);
  
  tft.init();
  tft.invertDisplay(0);
  tft.setRotation(3); // Try 1 or 3 for landscape orientation
  tft.fillScreen(BG_COLOR); // Initial screen clear in setup
  // Initial screen clear in setup
  tft.setCursor(20,20);
  tft.println("hello");
}

void loop(){
  static uint8_t b = 0;
  static bool b1 = false;
  while(Serial.available()) {
    tft.fillScreen(BG_COLOR); // Initial screen clear in setup
    tft.setCursor(20,20);
    b = Serial.read();
    b1 = true;
  }
  if(b1){
    //tft.println(String(b));
    b1 = false;

    if(b == 2 || b == '2') face=LISTEN;
    else if(b == 3 || b == '3') face=SPEAK;
    else face = IDLE;

  }

  switch(face){
    case LISTEN:
      animationListen();
    break;
    case SPEAK:
      animationSpeak();
    break;
    case IDLE:
      animationIdle();
  }
  //drawEyes();
  // delay(1500);
  // animationBlink();
  //animationListen();
  //animationSpeak();
}

void cleanEyes(int offx, int offy){
  tft.fillRoundRect(EYE_LEFT_POS_X+offx, EYE_POS_Y+offy, EYE_WIDTH, EYE_HEIGHT, EYE_CORNER_RADIUS, BG_COLOR);
  tft.fillRoundRect(EYE_RIGHT_POS_X+offx, EYE_POS_Y+offy, EYE_WIDTH, EYE_HEIGHT, EYE_CORNER_RADIUS, BG_COLOR);
}

void drawFace(int offx, int offy){
  drawEyes(offx, offy);
  drawSmile();
  // tft.drawLine(MOUTH_POS_X, MOUTH_POS_Y+0.65*MOUTH_HEIGHT, MOUTH_POS_X+MOUTH_WIDTH, MOUTH_POS_Y+0.65*MOUTH_HEIGHT, FG_COLOR);
  // tft.drawLine(MOUTH_POS_X, MOUTH_POS_Y+0.65*MOUTH_HEIGHT, MOUTH_POS_X-18, MOUTH_POS_Y+0.65*MOUTH_HEIGHT-15, FG_COLOR);
  // tft.drawLine(MOUTH_POS_X+MOUTH_WIDTH, MOUTH_POS_Y+0.65*MOUTH_HEIGHT, MOUTH_POS_X+MOUTH_WIDTH+18, MOUTH_POS_Y+0.65*MOUTH_HEIGHT-15, FG_COLOR);
}

void drawSmile(){
  tft.drawLine(MOUTH_SMILE_START_X, MOUTH_SMILE_POS_Y, MOUTH_SMILE_END_X, MOUTH_SMILE_POS_Y, FG_COLOR);
  tft.drawLine(MOUTH_SMILE_START_X, MOUTH_SMILE_POS_Y, MOUTH_SMILE_START_X-MOUTH_SMILE_DISPL_X, MOUTH_SMILE_POS_Y-MOUTH_SMILE_DISPL_Y, FG_COLOR);
  tft.drawLine(MOUTH_SMILE_END_X, MOUTH_SMILE_POS_Y, MOUTH_SMILE_END_X+MOUTH_SMILE_DISPL_X, MOUTH_SMILE_POS_Y-MOUTH_SMILE_DISPL_Y, FG_COLOR);
}

void drawEyes(int offx, int offy){
  tft.fillRoundRect(EYE_LEFT_POS_X+offx, EYE_POS_Y+offy, EYE_WIDTH, EYE_HEIGHT, EYE_CORNER_RADIUS, FG_COLOR);
  tft.fillRoundRect(EYE_RIGHT_POS_X+offx, EYE_POS_Y+offy, EYE_WIDTH, EYE_HEIGHT, EYE_CORNER_RADIUS, FG_COLOR);
}

void drawEyesBorder(int offx, int offy){
  tft.drawRoundRect(EYE_LEFT_POS_X+offx, EYE_POS_Y+offy, EYE_WIDTH, EYE_HEIGHT, EYE_CORNER_RADIUS, FG_COLOR);
  tft.drawRoundRect(EYE_RIGHT_POS_X+offx, EYE_POS_Y+offy, EYE_WIDTH, EYE_HEIGHT, EYE_CORNER_RADIUS, FG_COLOR);
}

void drawMouth(double phase1, double phase2, double phase3){  
  // Mouth is a sinusoidal function with dynamic amplitude
  tft.fillRect(MOUTH_POS_X, MOUTH_POS_Y, MOUTH_WIDTH, MOUTH_HEIGHT, BG_COLOR);
  int old_x{MOUTH_POS_X};
  int old_y{MOUTH_POS_Y + MOUTH_HEIGHT*0.4};
 
  for (int x = MOUTH_POS_X ; x < MOUTH_POS_X + MOUTH_WIDTH; x++){

    // Serial.print("x ");
    // Serial.println(x);
    double y1 = abs(x - phase1) > 1e-1 ? 35*sin(x - phase1)/(x - phase1) : 35;
    // Serial.print("y ");
    // Serial.println(y);
    double y2 = abs(x - phase2) > 1e-1 ? -35*sin(0.4*PI*(double)x - phase2)/(x - phase2) : -35;
    // Serial.print("y ");
    // Serial.println(y);
    double y3 = abs(x - phase3) > 1e-1 ? -25*sin(0.02*PI*x*x*x - phase3)/(x - phase3) : -25;
    int y = y1 + y2 + y3 + MOUTH_POS_Y + MOUTH_HEIGHT*0.4;
    
    tft.drawLine(old_x, old_y, x, y, FG_COLOR);
    old_x = x;
    old_y = y;
  }
}


void animationListen(){
  static elapsedMillis animTimer=0;
  static unsigned long waitTime=0;
  static bool state = false;

  if(animTimer >= waitTime){
    tft.fillScreen(BG_COLOR); // Initial screen clear in setup  
    state = !state;
    waitTime = 600 + random(4)*80;
    animTimer = 0;
  }

  if(state){
    drawEyes(65, EAR_POS_Y - EYE_POS_Y);
    tft.drawArc(62, EAR_POS_Y + EYE_HEIGHT*0.3 + EAR_SMALL_OUTER_RADIUS , EAR_SMALL_OUTER_RADIUS, EAR_SMALL_INNER_RADIUS, EAR_SMALL_START_ANGLE, EAR_SMALL_END_ANGLE, FG_COLOR, BG_COLOR, true);
    tft.drawArc(75, EAR_POS_Y + EAR_BIG_OUTER_RADIUS, EAR_BIG_OUTER_RADIUS, EAR_BIG_INNER_RADIUS, EAR_BIG_START_ANGLE, EAR_BIG_END_ANGLE, FG_COLOR, BG_COLOR, true);
  }else{
    drawEyes(-65, EAR_POS_Y - EYE_POS_Y);
    tft.drawArc(DISPLAY_WIDTH - 62 - EAR_SMALL_OUTER_RADIUS, EAR_POS_Y + EYE_HEIGHT*0.3 + EAR_SMALL_OUTER_RADIUS , EAR_SMALL_OUTER_RADIUS, EAR_SMALL_INNER_RADIUS, 360 - EAR_SMALL_END_ANGLE, 360 - EAR_SMALL_START_ANGLE, FG_COLOR, BG_COLOR, true);
    tft.drawArc(DISPLAY_WIDTH - 75 - EAR_SMALL_OUTER_RADIUS, EAR_POS_Y + EAR_BIG_OUTER_RADIUS, EAR_BIG_OUTER_RADIUS, EAR_BIG_INNER_RADIUS, 360 - EAR_BIG_END_ANGLE, 360 - EAR_BIG_START_ANGLE, FG_COLOR, BG_COLOR, true);
  }

}

void animationSpeak(){
  // tft.fillScreen(BG_COLOR); // Initial screen clear in setup  
  drawEyes();

  static double phase1{0};
  static double phase2{-16};
  static double phase3{13};
  static double offset1{19};
  static double offset2{-25};
  static double offset3{12};

  drawMouth(phase1 + 0.5*DISPLAY_WIDTH, phase2 + 0.5*DISPLAY_WIDTH, phase3 + 0.5*DISPLAY_WIDTH);

  if(phase1 > MOUTH_ACTIVE_WIDTH || phase1 < -MOUTH_ACTIVE_WIDTH) offset1 *= -1;
  if(phase2 > MOUTH_ACTIVE_WIDTH || phase2 < -MOUTH_ACTIVE_WIDTH) offset2 *= -1;
  if(phase3 > MOUTH_ACTIVE_WIDTH || phase3 < -MOUTH_ACTIVE_WIDTH) offset3 *= -1;

  phase1 += offset1;
  phase2 += offset2;
  phase3 += offset3;
  // Serial.print("phase1: ");
  // Serial.println(phase1);
}
 

void animationBlink(bool fullface) {
  if(fullface) drawFace();
  else drawEyes();

  for(int i = 0; i < random(1,2); i++){
    delay(350 + random(3)*50);
    elapsedMillis t = 0;
    elapsedMillis t1 = 0;
    while(t <= EYE_ANIM_BLINK_TOTAL_TIME){
      if(t1 < EYE_ANIM_BLINK_DRAW_TIME) continue;

      t1 = 0;
      // Serial.println(t);
      //int h =  max(EYE_CORNER_RADIUS*0.75, EYE_HEIGHT - EYE_HEIGHT / pow(2, 2 * (t/EYE_ANIM_BLINK_TOTAL_TIME)*1e-3));
      int h = EYE_HEIGHT / pow(2, 5 * (t/ (double)EYE_ANIM_BLINK_TOTAL_TIME));
      // Serial.println(h);

      tft.fillScreen(BG_COLOR); // Initial screen clear in setup  
      // cleanEyes(); // TODO: only clean eyes?
      
      drawEyesBorder();
      if(fullface) drawSmile();
      tft.fillRoundRect(EYE_LEFT_POS_X, EYE_POS_Y+EYE_HEIGHT-h, EYE_WIDTH, h, EYE_CORNER_RADIUS, TFT_GREEN);
      tft.fillRoundRect(EYE_RIGHT_POS_X, EYE_POS_Y+EYE_HEIGHT-h, EYE_WIDTH, h, EYE_CORNER_RADIUS, TFT_GREEN);
    }
    if(fullface) drawFace();
    else drawEyes();
  
  }
}

void animationIdle(){
  static elapsedMillis animTimer=0;
  static unsigned long waitTime=0;

  drawFace();
  if(animTimer >= waitTime){
    animationBlink(true);
    animTimer = 0;
    waitTime = 1800 + random(4)*300;
  }
}