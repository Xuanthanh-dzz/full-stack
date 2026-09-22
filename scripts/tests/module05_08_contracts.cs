using PatternShippingDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
Throws<ArgumentNullException>(()=>ShippingCalculator.Quote(null));Throws<ArgumentOutOfRangeException>(()=>ShippingCalculator.Quote(new DomesticShipment("A",0,true)));Check(ShippingCalculator.Quote(new DomesticShipment("A",2,true)).Fee==55000m,"boundary");Throws<NotSupportedException>(()=>ShippingCalculator.Quote(new DomesticShipment("A",2.01m,true)));Throws<ArgumentException>(()=>ShippingCalculator.Quote(new BulkShipment("A",[])));Throws<ArgumentOutOfRangeException>(()=>ShippingCalculator.Quote(new BulkShipment("A",[1,-1])));Check(ShippingCalculator.Quote(new BulkShipment("A",[1,2,3])).Fee==120000m,"bulk");
}
}
