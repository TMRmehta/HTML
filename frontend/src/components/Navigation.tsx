import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Stethoscope, Activity, LogIn, UserPlus, LogOut, User, Settings, Menu, X } from "lucide-react";
import { useState } from "react";
import LoginDialog from "@/components/auth/LoginDialog";
import SignupDialog from "@/components/auth/SignupDialog";
import { useAuthContext } from "@/context/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loginOpen, setLoginOpen] = useState(false);
  const [signupOpen, setSignupOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout, logoutLoading } = useAuthContext();
  console.log("Navigation component rendering, location:", location.pathname);

  return (
    <nav className="bg-white/95 backdrop-blur-sm border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 sm:space-x-3 group">
            <div className="bg-primary rounded-xl p-1.5 sm:p-2 group-hover:bg-primary-light transition-medical">
              <Activity className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-base sm:text-xl font-serif font-semibold text-foreground">
                OncoSight AI
              </span>
              <span className="text-xs sm:text-sm text-muted-foreground hidden sm:block">
                AI-Powered Medical Platform
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            {!isAuthenticated && (
              <Link
                to="/"
                className={`text-sm font-medium transition-smooth hover:text-primary ${
                  location.pathname === "/" ? "text-primary" : "text-muted-foreground"
                }`}
              >
                Home
              </Link>
            )}
            
            <RoleGuard requiredRoles={['PATIENT']}>
              <Link
                to="/patients"
                className={`text-sm font-medium transition-smooth hover:text-primary ${
                  location.pathname === "/patients" ? "text-primary" : "text-muted-foreground"
                }`}
              >
                Patient Portal
              </Link>
            </RoleGuard>
            
            <RoleGuard requiredRoles={['RESEARCHER']}>
              <Link
                to="/research"
                className={`text-sm font-medium transition-smooth hover:text-primary ${
                  location.pathname === "/research" ? "text-primary" : "text-muted-foreground"
                }`}
              >
                Research Portal
              </Link>
            </RoleGuard>
            
            <Link
              to="/about"
              className={`text-sm font-medium transition-smooth hover:text-primary ${
                location.pathname === "/about" ? "text-primary" : "text-muted-foreground"
              }`}
            >
              About
            </Link>
            
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <User className="h-4 w-4 mr-2" />
                      {user?.firstname} {user?.lastname}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-background z-50">
                    <DropdownMenuLabel>My Account</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate("/profile")}>
                      <User className="h-4 w-4 mr-2" />
                      Profile
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/settings")}>
                      <Settings className="h-4 w-4 mr-2" />
                      Settings
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout} disabled={logoutLoading}>
                      <LogOut className="h-4 w-4 mr-2" />
                      {logoutLoading ? "Signing Out..." : "Logout"}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setLoginOpen(true)}
                >
                  <LogIn className="h-4 w-4" />
                  Sign In
                </Button>
                <Button 
                  variant="medical" 
                  size="sm"
                  onClick={() => setSignupOpen(true)}
                >
                  <UserPlus className="h-4 w-4" />
                  Sign Up
                </Button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="sm" className="p-2">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[280px] sm:w-[350px] bg-background">
                <div className="flex flex-col space-y-6 mt-6">
                  {!isAuthenticated && (
                    <Link
                      to="/"
                      className={`text-base font-medium transition-smooth hover:text-primary ${
                        location.pathname === "/" ? "text-primary" : "text-muted-foreground"
                      }`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Home
                    </Link>
                  )}
                  
                  <RoleGuard requiredRoles={['PATIENT']}>
                    <Link
                      to="/patients"
                      className={`text-base font-medium transition-smooth hover:text-primary ${
                        location.pathname === "/patients" ? "text-primary" : "text-muted-foreground"
                      }`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Patient Portal
                    </Link>
                  </RoleGuard>
                  
                  <RoleGuard requiredRoles={['RESEARCHER']}>
                    <Link
                      to="/research"
                      className={`text-base font-medium transition-smooth hover:text-primary ${
                        location.pathname === "/research" ? "text-primary" : "text-muted-foreground"
                      }`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Research Portal
                    </Link>
                  </RoleGuard>
                  
                  <Link
                    to="/about"
                    className={`text-base font-medium transition-smooth hover:text-primary ${
                      location.pathname === "/about" ? "text-primary" : "text-muted-foreground"
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    About
                  </Link>
                  
                  <div className="pt-4 border-t space-y-3">
                    {isAuthenticated ? (
                      <>
                        <div className="flex items-center space-x-2 px-3 py-2 bg-muted rounded-lg">
                          <User className="h-4 w-4" />
                          <span className="text-sm font-medium">{user?.firstname} {user?.lastname}</span>
                        </div>
                        <Button 
                          variant="outline" 
                          className="w-full justify-start"
                          onClick={() => {
                            navigate("/profile");
                            setMobileMenuOpen(false);
                          }}
                        >
                          <User className="h-4 w-4 mr-2" />
                          Profile
                        </Button>
                        <Button 
                          variant="outline" 
                          className="w-full justify-start"
                          onClick={() => {
                            navigate("/settings");
                            setMobileMenuOpen(false);
                          }}
                        >
                          <Settings className="h-4 w-4 mr-2" />
                          Settings
                        </Button>
                        <Button 
                          variant="destructive" 
                          className="w-full justify-start"
                          onClick={() => {
                            logout();
                            setMobileMenuOpen(false);
                          }}
                          disabled={logoutLoading}
                        >
                          <LogOut className="h-4 w-4 mr-2" />
                          {logoutLoading ? "Signing Out..." : "Logout"}
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button 
                          variant="outline" 
                          className="w-full"
                          onClick={() => {
                            setLoginOpen(true);
                            setMobileMenuOpen(false);
                          }}
                        >
                          <LogIn className="h-4 w-4 mr-2" />
                          Sign In
                        </Button>
                        <Button 
                          variant="medical" 
                          className="w-full"
                          onClick={() => {
                            setSignupOpen(true);
                            setMobileMenuOpen(false);
                          }}
                        >
                          <UserPlus className="h-4 w-4 mr-2" />
                          Sign Up
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
      
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
    </nav>
  );
};

export default Navigation;