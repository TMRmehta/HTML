import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Heart, 
  Microscope, 
  User, 
  Settings, 
  LogOut, 
  Calendar,
  TrendingUp,
  FileText,
  Users
} from "lucide-react";
import Navigation from "@/components/Navigation";
import { useAuthContext } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const { user, logout, logoutLoading } = useAuthContext();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  // Redirect users to their appropriate portal
  useEffect(() => {
    if (user) {
      switch (user.user_type) {
        case "PATIENT":
          navigate("/patients");
          break;
        case "RESEARCHER":
          navigate("/research");
          break;
        default:
          navigate("/patients");
      }
    }
  }, [user, navigate]);

  const getWelcomeMessage = () => {
    if (!user) return "Welcome";
    
    const roleMessages = {
      PATIENT: "Welcome to your patient portal",
      RESEARCHER: "Welcome to your research dashboard"
    };
    
    return roleMessages[user.user_type] || "Welcome";
  };

  const getQuickActions = () => {
    if (!user) return [];
    
    const baseActions = [];
    
    baseActions.push({
      title: "Patient Portal",
      description: "Access health information and support",
      icon: Heart,
      href: "/patients",
      color: "text-accent"
    });

    if (user.user_type === "RESEARCHER") {
      baseActions.push({
        title: "Research Portal", 
        description: "Search medical literature and trials",
        icon: Microscope,
        href: "/research",
        color: "text-trust"
      });
    }

    return baseActions;
  };

  const getStats = () => {
    if (!user) return [];
    
    const baseStats = [
      {
        title: "Account Status",
        value: user.is_verified ? "Verified" : "Pending",
        icon: User,
        color: user.is_verified ? "text-green-600" : "text-yellow-600"
      },
      {
        title: "Member Since",
        value: new Date(user.signup_timestamp).toLocaleDateString(),
        icon: Calendar,
        color: "text-muted-foreground"
      }
    ];

    if (user.last_login) {
      baseStats.push({
        title: "Last Login",
        value: new Date(user.last_login).toLocaleDateString(),
        icon: TrendingUp,
        color: "text-muted-foreground"
      });
    }

    return baseStats;
  };

  return (
    <div className="min-h-screen bg-subtle-gradient">
      <Navigation />
      
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-serif font-bold text-foreground mb-2">
                  {getWelcomeMessage()}
                </h1>
                <p className="text-lg text-muted-foreground">
                  {user?.firstname} {user?.lastname}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="secondary" className="capitalize">
                    {user?.user_type?.toLowerCase()}
                  </Badge>
                  {user?.is_verified && (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Verified
                    </Badge>
                  )}
                </div>
              </div>
              <Button variant="outline" onClick={handleLogout} disabled={logoutLoading}>
                <LogOut className="h-4 w-4" />
                {logoutLoading ? "Signing Out..." : "Sign Out"}
              </Button>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Quick Actions */}
              <Card className="card-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-4">
                    {getQuickActions().map((action, index) => {
                      const IconComponent = action.icon;
                      return (
                        <Button
                          key={index}
                          variant="outline"
                          className="h-auto p-4 flex flex-col items-start text-left hover:shadow-md transition-medical"
                          onClick={() => navigate(action.href)}
                        >
                          <div className="flex items-center gap-3 mb-2">
                            <IconComponent className={`h-5 w-5 ${action.color}`} />
                            <span className="font-semibold">{action.title}</span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {action.description}
                          </p>
                        </Button>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card className="card-shadow">
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-3 bg-secondary/50 rounded-lg">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium">Account created</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(user?.signup_timestamp || "").toLocaleString()}
                        </p>
                      </div>
                    </div>
                    {user?.last_login && (
                      <div className="flex items-center gap-3 p-3 bg-secondary/50 rounded-lg">
                        <div className="w-2 h-2 bg-accent rounded-full"></div>
                        <div>
                          <p className="text-sm font-medium">Last login</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(user.last_login).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Account Stats */}
              <Card className="card-shadow">
                <CardHeader>
                  <CardTitle>Account Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {getStats().map((stat, index) => {
                    const IconComponent = stat.icon;
                    return (
                      <div key={index} className="flex items-center gap-3">
                        <IconComponent className={`h-4 w-4 ${stat.color}`} />
                        <div>
                          <p className="text-sm font-medium">{stat.title}</p>
                          <p className={`text-xs ${stat.color}`}>{stat.value}</p>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Account Settings */}
              <Card className="card-shadow">
                <CardHeader>
                  <CardTitle>Account Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button variant="outline" className="w-full justify-start">
                    <Settings className="h-4 w-4" />
                    Profile Settings
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <User className="h-4 w-4" />
                    Account Preferences
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
