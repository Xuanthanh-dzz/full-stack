using DependencyInjectionDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var clock=new FixedClock(DateTimeOffset.UnixEpoch);var root=new CompositionRoot(clock);var first=root.BeginRequest("req-1");var second=root.BeginRequest("req-2");
 Check(!ReferenceEquals(first.CreateHandler(),first.CreateHandler()),"transient inside scope");Check(ReferenceEquals(first.Audit,first.Audit) && !ReferenceEquals(first.Audit,second.Audit),"scoped identities");
 Check(first.CreateHandler().Handle("a",1)=="placed" && second.CreateHandler().Handle("a",1)=="duplicate","shared store");
 Check(root.Log.Entries.SequenceEqual(new[]{"[req-1] placed a","[req-2] duplicate a"}),"correlation IDs");
 var other=new CompositionRoot(clock);Check(other.Store.Count==0 && !ReferenceEquals(root.Store,other.Store),"singleton per root");

 }

}
