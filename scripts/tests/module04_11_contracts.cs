using StructEnumTupleDemo;
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var a=new Money(5m,"vnd");var b=a.Add(2m);Check(a.Amount==5m&&b.Amount==7m,"value copy");
Check(default(Money).Currency is null,"default bypasses constructor");
Throws<ArgumentOutOfRangeException>(()=>a.Add(-6));Throws<ArgumentOutOfRangeException>(()=>ShippingCalculator.Calculate(1,(DeliveryOptions)8));
var fee=ShippingCalculator.Calculate(1200,DeliveryOptions.SignatureRequired|DeliveryOptions.Fragile);Check(fee.Fee.Amount==52000m&&fee.EstimatedDays==3,"combined flags");
Check(ShippingCalculator.Calculate(1,DeliveryOptions.Weekend).EstimatedDays==1,"weekend flag");
 }
}
