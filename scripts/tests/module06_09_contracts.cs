using CouplingCohesionDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var rates=new ShippingRates(500000,20000,35000,25000,60000);var normal=new ShippingCalculator(rates,"Ha Noi");var strict=new ShippingCalculator(rates with {FreeThreshold=1000000},"Ha Noi");
 var q=new ShippingQuoteRequest(500000,"Ha Noi",ShippingSpeed.Standard);Check(normal.Quote(q)==0 && strict.Quote(q)==20000 && normal.Quote(q)==0,"isolated configs");
 Check(normal.Quote(q with {Subtotal=499999})==20000 && normal.Quote(q with {Speed=ShippingSpeed.Express})==25000,"threshold and surcharge");
 Throws<ArgumentOutOfRangeException>(()=>normal.Quote(q with {Speed=(ShippingSpeed)99}));
 var lines=new List<OrderLine>{new("a",1,10)};var o=new Order("a","Ha Noi",lines);lines.Clear();Check(o.Subtotal==10,"input copied");

 }

}
