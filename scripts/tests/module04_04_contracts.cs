using System.Reflection;
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var reserve=typeof(CheckoutMethods.Program).GetMethod("TryReserveItem",BindingFlags.Static|BindingFlags.NonPublic)!;
object[] args={"X",decimal.MaxValue,2,10,0m,""};
Check(!(bool)reserve.Invoke(null,args)! && (int)args[3]==10 && (decimal)args[4]==0,"overflow must not reserve");
args=["X",5m,2,10,0m,""];Check((bool)reserve.Invoke(null,args)! && (int)args[3]==8 && (decimal)args[4]==10m,"valid reserve");
args=["X",5m,0,10,0m,""];Check(!(bool)reserve.Invoke(null,args)! && (int)args[3]==10,"zero rejected");
 }
}
