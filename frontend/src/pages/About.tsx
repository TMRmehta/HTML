import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Shield, Users, Lightbulb, ExternalLink, AlertTriangle } from "lucide-react";
import Navigation from "@/components/Navigation";

const About = () => {
  return (
    <div className="min-h-screen bg-subtle-gradient">
      <Navigation />
      
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-serif font-bold text-foreground mb-4">
              About OncoSight AI
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Advancing cancer research and patient care through AI-powered medical information platforms
            </p>
          </div>

          {/* Mission */}
          <Card className="card-shadow mb-8">
            <CardContent className="p-8">
              <h2 className="text-2xl font-serif font-semibold text-foreground mb-4">Our Mission</h2>
              <p className="text-foreground leading-relaxed mb-4">
                OncoSight AI is dedicated to bridging the gap between cutting-edge cancer research 
                and accessible patient information. Our AI-powered platform connects researchers, 
                healthcare professionals, and patients with the latest medical knowledge and clinical insights.
              </p>
              <p className="text-foreground leading-relaxed">
                We believe that informed patients and connected researchers can accelerate breakthroughs 
                in cancer treatment and improve outcomes for millions of people worldwide.
              </p>
            </CardContent>
          </Card>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <Card className="card-shadow border-primary/10">
              <CardContent className="p-6 text-center">
                <div className="bg-primary/10 rounded-full p-3 w-fit mx-auto mb-4">
                  <Lightbulb className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">AI-Powered Insights</h3>
                <p className="text-sm text-muted-foreground">
                  Advanced language models provide intelligent responses based on the latest medical research
                </p>
              </CardContent>
            </Card>

            <Card className="card-shadow border-accent/10">
              <CardContent className="p-6 text-center">
                <div className="bg-accent/10 rounded-full p-3 w-fit mx-auto mb-4">
                  <Users className="h-6 w-6 text-accent" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">Dual Portal System</h3>
                <p className="text-sm text-muted-foreground">
                  Separate interfaces designed specifically for patients and researchers
                </p>
              </CardContent>
            </Card>

            <Card className="card-shadow border-trust/10">
              <CardContent className="p-6 text-center">
                <div className="bg-trust/10 rounded-full p-3 w-fit mx-auto mb-4">
                  <Shield className="h-6 w-6 text-trust" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">Trusted Sources</h3>
                <p className="text-sm text-muted-foreground">
                  Connected to verified medical databases, clinical trials, and peer-reviewed research
                </p>
              </CardContent>
            </Card>
          </div>

          {/* External Links */}
          <Card className="card-shadow mb-8">
            <CardContent className="p-8">
              <h2 className="text-2xl font-serif font-semibold text-foreground mb-6">Trusted Medical Resources</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <Button variant="outline" className="justify-between h-auto p-4">
                  <div className="text-left">
                    <div className="font-medium">National Cancer Institute</div>
                    <div className="text-sm text-muted-foreground">🔃 Integration In Progress</div>
                  </div>
                  <ExternalLink className="h-4 w-4" />
                </Button>
                
                <Button variant="outline" className="justify-between h-auto p-4">
                  <div className="text-left">
                    <div className="font-medium">ClinicalTrials.gov</div>
                    <div className="text-sm text-muted-foreground">🔃 Integration In Progress</div>
                  </div>
                  <ExternalLink className="h-4 w-4" />
                </Button>
                
                <Button variant="outline" className="justify-between h-auto p-4">
                  <div className="text-left">
                    <div className="font-medium">PLOS Database</div>
                    <div className="text-sm text-muted-foreground">✅ Integration Active</div>
                  </div>
                  <ExternalLink className="h-4 w-4" />
                </Button>
                
                <Button variant="outline" className="justify-between h-auto p-4">
                  <div className="text-left">
                    <div className="font-medium">American Cancer Society</div>
                    <div className="text-sm text-muted-foreground">🔃 Integration In Progress</div>
                  </div>
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Important Disclaimers */}
          <Card className="card-shadow border-destructive/20 bg-destructive/5">
            <CardContent className="p-8">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-6 w-6 text-destructive flex-shrink-0 mt-1" />
                <div>
                  <h2 className="text-xl font-serif font-semibold text-foreground mb-4">
                    Important Medical Disclaimers
                  </h2>
                  <div className="space-y-3 text-foreground">
                    <p className="font-medium">
                      Not a Substitute for Professional Medical Advice
                    </p>
                    <p className="text-sm">
                      The information provided through this platform is for educational and informational 
                      purposes only. It is not intended to be a substitute for professional medical advice, 
                      diagnosis, or treatment.
                    </p>
                    
                    <p className="font-medium mt-4">
                      Always Consult Healthcare Professionals
                    </p>
                    <p className="text-sm">
                      Always seek the advice of your physician or other qualified health provider with 
                      any questions you may have regarding a medical condition. Never disregard professional 
                      medical advice or delay in seeking it because of something you have read on this platform.
                    </p>
                    
                    <p className="font-medium mt-4">
                      Emergency Situations
                    </p>
                    <p className="text-sm">
                      If you think you may have a medical emergency, call your doctor or emergency services 
                      immediately. This platform does not provide emergency medical services.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Feedback Section */}
          <div className="text-center mt-12 p-8 bg-background rounded-lg card-shadow">
            <p className="text-lg text-muted-foreground mb-6">
              Help us improve this platform for everyone by giving your valuable feedback
            </p>
            <Button 
              variant="outline" 
              size="lg"
              onClick={() => window.open('https://forms.gle/Zzi9JfWGkbjB5XoS8', '_blank')}
            >
              Submit Feedback
              <ExternalLink className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;