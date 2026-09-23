using DependencyInversionDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var store=new InMemoryOrderStore();var notify=new CollectingNotifier();var clock=new Clock();var service=new PlaceOrderService(store,notify,clock,100);
 Check(service.Place("a","c",10).Outcome==PlaceOutcome.Placed && clock.Reads==1,"placed and clock read once");
 Check(service.Place("a","c",10).Outcome==PlaceOutcome.Duplicate && notify.Sent.Count==1 && clock.Reads==1,"duplicate no clock/notify");
 Check(service.Place("b","c",101).Outcome==PlaceOutcome.Rejected && store.Orders.Count==1,"limit before save");
 var faulty=new PlaceOrderService(store,new FaultNotifier(),clock,100);Throws<IOException>(()=>faulty.Place("b","c",10));Check(store.Exists("b"),"notification failure after persistence");
 var fixedClock=new FixedClock(new DateTimeOffset(2026,1,1,7,0,0,TimeSpan.FromHours(7)));Check(fixedClock.UtcNow.Offset==TimeSpan.Zero && fixedClock.UtcNow.Hour==0,"UTC normalization");

 }

 sealed class Clock:IClock {public int Reads;public DateTimeOffset UtcNow {get{Reads++;return new DateTimeOffset(2026,1,1,0,0,0,TimeSpan.Zero);}}}
 sealed class FaultNotifier:ICustomerNotifier {public void OrderPlaced(PlacedOrder o)=>throw new IOException();}

}
