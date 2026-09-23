using SingleResponsibilityDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var parser=new OrderLineParser();var pricing=new PricingPolicy(.08m,1000000,.05m);var store=new InMemoryReceiptStore();
 var use=new PlaceOrderUseCase(parser,pricing,new ReceiptFormatter(),store);
 var p=pricing.Calculate(parser.Parse("X:1:1000000"));Check(p==new PriceBreakdown(1000000,50000,76000,1026000),"threshold oracle");
 Check(pricing.Calculate(parser.Parse("X:1:999999")).Discount==0,"under threshold");
 Throws<FormatException>(()=>use.Execute("A","X:0:1"));Throws<FormatException>(()=>use.Execute("A"," :1:1"));Check(store.Saved.Count==0,"parse rejection no save");
 use.Execute("A","X:1:1");use.Execute("A","X:1:2");Check(store.Saved.Count==1,"documented overwrite");
 Throws<ArgumentOutOfRangeException>(()=>new PricingPolicy(0,0,1.01m));

 }

}
