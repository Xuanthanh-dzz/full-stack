
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
ShippingMethod a=new ExpressShipping(2);Check(a.CalculateFee(2.5m)==105000m,"virtual dispatch");
Check(new StorePickup("A").CalculateFee(1m)==0m,"pickup");Throws<ArgumentOutOfRangeException>(()=>a.CalculateFee(0));
Throws<ArgumentOutOfRangeException>(()=>new ExpressShipping(4));
ShippingMethod b=new InternationalExpressShipping("SG",1);Check(b.CalculateFee(2.5m)==195000m,"sealed override");
 }
}
