import LoginForm from "@/components/customs/Auth/LoginForm";
import logo from "@/assets/logo.png";

const Auth = () => {
  return (
    <div className="login-background relative flex min-h-screen items-center justify-center p-4">
      <div className="form-container w-full max-w-sm space-y-6 p-8 relative z-10">
        <div className="flex flex-col items-center space-y-4 text-center text-white">
          <img
            src={logo}
            alt="SMART FARM Logo"
            className="w-32 h-32 object-cover rounded-full border-4 border-white/80 shadow-[0_0_20px_rgba(0,255,128,0.5)] mb-4"
          />
          <h1 className="text-3xl font-bold tracking-tight">SMART FARM</h1>
          <h2 className="text-2xl">Login</h2>
        </div>
        <div className="text-white">
          <LoginForm />
        </div>
        <p className="px-8 text-center text-sm text-gray-200">
          By clicking continue, you agree to our{" "}
          <a
            href="#"
            className="hover:text-white underline underline-offset-4"
            onClick={(e) => e.preventDefault()}
          >
            Terms of Service
          </a>{" "}
          and{" "}
          <a
            href="#"
            className="hover:text-white underline underline-offset-4"
            onClick={(e) => e.preventDefault()}
          >
            Privacy Policy
          </a>
          .
        </p>
      </div>
    </div>
  );
};
export default Auth;
