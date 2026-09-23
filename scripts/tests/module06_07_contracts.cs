using InterfaceSegregationDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var store=new InMemoryOrderStore();var d=new DateOnly(2026,7,1);store.Save(new OrderSummary("a","c",1,d.AddDays(-1)));store.Save(new OrderSummary("b","c",1,d));
 var old=store.Find("a")!;Check(store.ArchiveOlderThan(d)==1 && store.ArchiveOlderThan(d)==0,"strict cutoff and repeat");
 Check(!old.Archived && store.Find("a")!.Archived && !store.Find("b")!.Archived && store.Count==2,"new record not mutation/delete");
 Check(store.Find("A")==null,"ordinal IDs");
 var writer=new Writer();new PlaceOrderHandler(writer).Handle("x","c",5,d);Check(writer.Saved?.Total==5,"writer-only double");
 Throws<ArgumentOutOfRangeException>(()=>new PlaceOrderHandler(writer).Handle("x","c",-1,d));

 }
 sealed class Writer:IOrderWriter {public OrderSummary? Saved;public void Save(OrderSummary o)=>Saved=o;}
}
