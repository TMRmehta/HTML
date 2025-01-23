import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { Users, Search, Shield, Stethoscope, Microscope, Heart, ArrowRight, CheckCircle, LogIn, UserPlus } from "lucide-react";
import Navigation from "@/components/Navigation";
import LoginDialog from "@/components/auth/LoginDialog";
import SignupDialog from "@/components/auth/SignupDialog";
import { useState } from "react";
import heroImage from "@/assets/medical-hero.jpg";

const Index = () => {
  const [loginOpen, setLoginOpen] = useState(false);
  const [signupOpen, setSignupOpen] = useState(false);
  console.log("Index component rendering");
  console.log("heroImage:", heroImage);
  
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative py-12 sm:py-16 md:py-20 overflow-hidden">
        <div className="absolute inset-0 subtle-gradient"></div>
        <div className="relative container mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-8 md:gap-12 items-center">
            <div className="space-y-6 sm:space-y-8">
              <div className="space-y-3 sm:space-y-4">
                <Badge className="bg-primary/10 text-primary border-primary/20 text-xs sm:text-sm">
                  AI-Powered Medical Research Platform
                </Badge>
                <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-serif font-bold text-foreground leading-tight">
                  Advancing Cancer
                  <span className="text-primary"> Research</span> with AI
                </h1>
                <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed">
                  Connecting patients and researchers with the latest medical knowledge through 
                  our AI-powered platform. Get instant access to clinical trials, research papers, 
                  and patient testimonials.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Button 
                  variant="medical" 
                  size="lg" 
                  className="w-full sm:w-auto text-sm sm:text-base"
                  onClick={() => setLoginOpen(true)}
                >
                  <Heart className="h-4 w-4 sm:h-5 sm:w-5" />
                  For Patients
                  <ArrowRight className="h-3 w-3 sm:h-4 sm:w-4" />
                </Button>
                <Button 
                  variant="trust" 
                  size="lg" 
                  className="w-full sm:w-auto text-sm sm:text-base"
                  onClick={() => setLoginOpen(true)}
                >
                  <Microscope className="h-4 w-4 sm:h-5 sm:w-5" />
                  For Researchers
                  <ArrowRight className="h-3 w-3 sm:h-4 sm:w-4" />
                </Button>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-2 sm:pt-4">
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="w-full sm:w-auto text-sm"
                  onClick={() => setLoginOpen(true)}
                >
                  <LogIn className="h-4 w-4 sm:h-5 sm:w-5" />
                  Sign In to Your Account
                </Button>
                <Button 
                  variant="secondary" 
                  size="lg" 
                  className="w-full sm:w-auto text-sm"
                  onClick={() => setSignupOpen(true)}
                >
                  <UserPlus className="h-4 w-4 sm:h-5 sm:w-5" />
                  Create New Account
                </Button>
              </div>
              
              <div className="flex flex-wrap items-center gap-3 sm:gap-6 text-xs sm:text-sm text-muted-foreground">
                <div className="flex items-center space-x-1.5 sm:space-x-2">
                  <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-accent flex-shrink-0" />
                  <span>Research Backed</span>
                </div>
                <div className="flex items-center space-x-1.5 sm:space-x-2">
                  <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-accent flex-shrink-0" />
                  <span>Peer-Reviewed Sources</span>
                </div>
                <div className="flex items-center space-x-1.5 sm:space-x-2">
                  <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-accent flex-shrink-0" />
                  <span>Real-Time Updates</span>
                </div>
              </div>
            </div>
            
            <div className="relative hidden lg:block">
              <div className="absolute inset-0 medical-gradient rounded-3xl transform rotate-6 opacity-20"></div>
              <img 
                src={heroImage} 
                alt="Medical research laboratory" 
                className="relative rounded-3xl hero-shadow w-full h-auto"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Demo Videos Section */}
      <section className="py-12 sm:py-16 md:py-20 bg-muted/30">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif font-bold text-foreground mb-3 sm:mb-4">
              See Our Platform in Action
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto px-4">
              Watch how our AI-powered platform helps patients and researchers access critical cancer research information.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6 sm:gap-8 max-w-6xl mx-auto">
            <div className="relative rounded-xl overflow-hidden shadow-lg aspect-video">
              <iframe
                src="https://www.youtube.com/embed/CuEG1Manhrw"
                title="Demo Video 1"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="absolute inset-0 w-full h-full"
              />
            </div>
            <div className="relative rounded-xl overflow-hidden shadow-lg aspect-video">
              <iframe
                src="https://www.youtube.com/embed/Pqaex5LQS9U"
                title="Demo Video 2"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="absolute inset-0 w-full h-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 sm:py-16 md:py-20 bg-white">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif font-bold text-foreground mb-3 sm:mb-4">
              Trusted by Medical Professionals
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto px-4">
              Our platform provides reliable, evidence-based information for both patients 
              seeking support and researchers advancing cancer treatment.
            </p>
          </div>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            <Card className="card-shadow border-primary/10 hover:shadow-lg transition-medical">
              <CardContent className="p-8 text-center">
                <div className="bg-primary/10 rounded-full p-4 w-fit mx-auto mb-6">
                  <Users className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-serif font-semibold text-foreground mb-4">
                  Patient Support Portal
                </h3>
                <p className="text-muted-foreground mb-6">
                  Get compassionate, AI-powered responses to your health questions with 
                  appropriate disclaimers and professional guidance.
                </p>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => setLoginOpen(true)}
                >
                  Access Patient Portal
                </Button>
              </CardContent>
            </Card>
            
            <Card className="card-shadow border-accent/10 hover:shadow-lg transition-medical">
              <CardContent className="p-8 text-center">
                <div className="bg-accent/10 rounded-full p-4 w-fit mx-auto mb-6">
                  <Search className="h-8 w-8 text-accent" />
                </div>
                <h3 className="text-xl font-serif font-semibold text-foreground mb-4">
                  Research Portal
                </h3>
                <p className="text-muted-foreground mb-6">
                  Advanced search capabilities with AI-powered insights, citations, 
                  and connections to leading medical databases.
                </p>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => setLoginOpen(true)}
                >
                  Access Research Portal
                </Button>
              </CardContent>
            </Card>
            
            <Card className="card-shadow border-trust/10 hover:shadow-lg transition-medical">
              <CardContent className="p-8 text-center">
                <div className="bg-trust/10 rounded-full p-4 w-fit mx-auto mb-6">
                  <Shield className="h-8 w-8 text-trust" />
                </div>
                <h3 className="text-xl font-serif font-semibold text-foreground mb-4">
                  Trusted Sources
                </h3>
                <p className="text-muted-foreground mb-6">
                  Connected to verified medical databases, clinical trials, 
                  and peer-reviewed research from trusted institutions.
                </p>
                <Link to="/about">
                  <Button variant="outline" className="w-full">
                    Learn More
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-16 md:py-20 medical-gradient">
        <div className="container mx-auto px-4 sm:px-6 text-center">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif font-bold text-white mb-4 sm:mb-6">
              Ready to Get Started?
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-white/90 mb-6 sm:mb-8 px-4">
              Join many other patients and researchers using our platform to 
              access the latest cancer research and treatment information.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
              <Button 
                variant="secondary" 
                size="lg" 
                className="w-full sm:w-auto"
                onClick={() => setLoginOpen(true)}
              >
                <Stethoscope className="h-5 w-5" />
                Start as Patient
              </Button>
              <Button 
                variant="outline" 
                size="lg" 
                className="w-full sm:w-auto border-white hover:bg-white hover:text-primary"
                onClick={() => setLoginOpen(true)}
              >
                <Microscope className="h-5 w-5" />
                Start as Researcher
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Feedback Section */}
      <section className="py-12 sm:py-16 bg-background">
        <div className="container mx-auto px-4 sm:px-6 text-center">
          <div className="max-w-2xl mx-auto">
            <p className="text-base sm:text-lg text-muted-foreground mb-6">
              Help us improve this platform for everyone by giving your valuable feedback
            </p>
            <Button 
              variant="outline" 
              size="lg" 
              className="w-full sm:w-auto"
              onClick={() => window.open('https://forms.gle/Zzi9JfWGkbjB5XoS8', '_blank')}
            >
              Submit Feedback
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      </section>
      
      <LoginDialog
        open={loginOpen} 
        onOpenChange={setLoginOpen} 
      />
      <SignupDialog 
        open={signupOpen} 
        onOpenChange={setSignupOpen}
        onSignupSuccess={() => {
          console.log("Signup successful, user will be redirected");
        }}
      />
    </div>
  );
};

export default Index;
